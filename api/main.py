import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.errors import HttpError
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai.classifier import classify_email
from database import SessionLocal, init_database, get_db
from gmail.email_parser import extract_email_content
from gmail.gmail_service import (
    create_gmail_watch,
    get_added_message_ids,
    get_gmail_service,
    get_gmail_service_for_user,
    get_message,
)
from gmail.pubsub import parse_pubsub_notification
from models import Email, User
from repository import save_classified_email
from api.schemas import (
    ConnectGmailTokenRequest,
    EmailResponse,
    GoogleCodeRequest,
    GoogleLoginRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    StatsResponse,
    TokenResponse,
    UserResponse,
)
from api.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user_from_db,
    hash_password,
    normalize_email,
    revoke_refresh_token,
    verify_and_rotate_refresh_token,
    verify_google_token,
    verify_password,
)

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token


bearer_scheme = HTTPBearer()

app = FastAPI(
    title="Email Classifier API",
    version="3.0.0",
)

# ==================================================
# CORS
# ==================================================

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://localhost:8000",
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:8000",
#         "http://localhost",
#         "http://127.0.0.1",
#     ],
#     allow_origin_regex=r"https?://.*",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# Comma-separated list of allowed frontend origins.
# Local development is included by default.
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173",
)

allowed_origins = [
    origin.strip().rstrip("/")
    for origin in frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# Configuration
# ==================================================

HISTORY_ID_FILE = os.getenv(
    "GMAIL_HISTORY_ID_FILE",
    "gmail_state/gmail_history_id.txt",
)

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")


# ==================================================
# Startup
# ==================================================

@app.on_event("startup")
def create_tables() -> None:
    init_database()





# ==================================================
# Gmail Owner User Helper
# ==================================================

def get_owner_user(db: Session) -> User | None:
    """Retrieve or create the default owner User for Gmail webhook classification."""
    if not OWNER_EMAIL:
        return None
    clean_owner = normalize_email(OWNER_EMAIL)
    if not clean_owner:
        return None

    owner = db.scalar(select(User).where(User.email == clean_owner))
    if not owner:
        owner = User(
            email=clean_owner,
            name="Owner",
            is_active=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
    return owner


# ==================================================
# Gmail utility functions
# ==================================================

def get_headers(message: dict) -> dict[str, str]:
    return {
        header["name"].lower(): header["value"]
        for header in message.get("payload", {}).get("headers", [])
    }


def parse_received_at(value: str | None):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def load_history_id() -> str | None:
    if not os.path.exists(HISTORY_ID_FILE):
        return None
    try:
        with open(HISTORY_ID_FILE, "r", encoding="utf-8") as file:
            value = file.read().strip()
        return value if value else None
    except OSError as error:
        print("Could not read history ID file:", error)
        return None


def save_history_id(history_id: str) -> None:
    directory = os.path.dirname(HISTORY_ID_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(HISTORY_ID_FILE, "w", encoding="utf-8") as file:
        file.write(str(history_id))


# ==================================================
# Process one Gmail message
# ==================================================

def process_single_message(service, db: Session, message_id: str, user_id: int | None = None):
    print("\n" + "=" * 60)
    print("PROCESSING MESSAGE")
    print("=" * 60)
    print("Message ID:", message_id)

    try:
        message = get_message(service, message_id)
    except HttpError as error:
        if error.resp.status == 404:
            print("Message no longer exists in Gmail:", message_id)
            return False
        raise

    headers = get_headers(message)
    sender = headers.get("from", "")
    subject = headers.get("subject", "")
    content = extract_email_content(message.get("payload", {}))
    body = content["body"]

    print("Thread ID:", message.get("threadId"))
    print("FROM:", sender)
    print("SUBJECT:", subject)

    # Resolve target user ID for classification ownership
    if not user_id:
        owner = get_owner_user(db)
        user_id = owner.id if owner else None

    existing_email = (
        db.query(Email.id)
        .filter_by(gmail_message_id=message_id, user_id=user_id)
        .first()
    )
    if existing_email:
        print("Skipped already-saved message for user:", message_id)
        return False

    print("Classifying email with Groq...")
    classification = classify_email(subject=subject, body=body)

    print("\nAI CLASSIFICATION")
    print("-" * 30)
    print("Category:", classification.category)
    print("Priority:", classification.priority)
    print("Sentiment:", classification.sentiment)
    print("Summary:", classification.summary)
    print("Requires response:", classification.requires_response)

    email, created = save_classified_email(
        db,
        gmail_message_id=message_id,
        gmail_thread_id=message.get("threadId"),
        sender=sender,
        subject=subject,
        body=body,
        received_at=parse_received_at(headers.get("date")),
        classification=classification,
        user_id=user_id,
    )

    if created:
        print("Saved:", email.subject or "(no subject)")
    else:
        print("Skipped:", email.subject or "(no subject)")

    return created


def process_history(service, previous_history_id: str, user_id: int | None = None):
    print("\n" + "=" * 60)
    print("PROCESSING GMAIL HISTORY")
    print("=" * 60)
    print("Starting history ID:", previous_history_id)

    try:
        message_ids = get_added_message_ids(service, previous_history_id)
    except HttpError as error:
        if error.resp.status == 404:
            print("\nWARNING: Gmail history ID is stale.")
            print("Invalid history ID:", previous_history_id)
            return False
        raise

    print("New messages found:", len(message_ids))
    if not message_ids:
        return True

    with SessionLocal() as db:
        for message_id in message_ids:
            try:
                process_single_message(service, db, message_id, user_id=user_id)
            except HttpError as error:
                if error.resp.status == 404:
                    print("Message unavailable:", message_id)
                    continue
                raise
            except Exception as error:
                print("\nERROR processing message:", message_id)
                print(error)
                raise
    return True


def setup_watch_for_user(user: User, db: Session) -> dict:
    """Helper to create or renew Gmail watch for a specific user and save state to DB."""
    topic = os.getenv("GMAIL_PUBSUB_TOPIC")
    if not topic:
        raise HTTPException(status_code=400, detail="GMAIL_PUBSUB_TOPIC is not configured")

    if user.gmail_refresh_token:
        service = get_gmail_service_for_user(user.gmail_refresh_token)
    else:
        service = get_gmail_service()

    response = create_gmail_watch(service, topic)
    new_history_id = response.get("historyId")
    expiration = response.get("expiration")

    if new_history_id:
        user.gmail_history_id = str(new_history_id)
        if expiration:
            from datetime import datetime, timezone
            user.gmail_watch_expiration = datetime.fromtimestamp(int(expiration) / 1000.0, tz=timezone.utc)
        db.commit()
        db.refresh(user)

    return response


# ==================================================
# Root & Webhook
# ==================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Email Classifier API",
    }


# ==================================================
# Health
# ==================================================

@app.get("/health")
def health():
    """Health check endpoint for Cloud Run / load balancers."""
    return {"status": "ok"}


def background_process_user_history(user_id: int, previous_history_id: str, new_history_id: str):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            return
        try:
            if user.gmail_refresh_token:
                service = get_gmail_service_for_user(user.gmail_refresh_token)
            else:
                service = get_gmail_service(interactive=False)

            history_processed = process_history(service, previous_history_id, user_id=user.id)
            if history_processed:
                user.gmail_history_id = str(new_history_id)
                db.commit()
        except FileNotFoundError as fnf_err:
            print(f"Skipping background history processing for {user.email}: {fnf_err}")
        except Exception as error:
            print(f"\nERROR in background Gmail history processing for {user.email}:", error)


def background_process_fallback_history(previous_history_id: str, new_history_id: str):
    try:
        service = get_gmail_service(interactive=False)
        history_processed = process_history(service, previous_history_id)
        if history_processed:
            save_history_id(new_history_id)
    except FileNotFoundError as fnf_err:
        print("Skipping fallback Gmail history processing:", fnf_err)
    except Exception as error:
        print("\nERROR in background fallback Gmail history processing:", error)


PUBSUB_PUSH_AUDIENCE = os.getenv("PUBSUB_PUSH_AUDIENCE", "")
PUBSUB_PUSH_SERVICE_ACCOUNT = os.getenv(
    "PUBSUB_PUSH_SERVICE_ACCOUNT",
    "",
)


def verify_pubsub_push(request: Request) -> None:
    """Verify the OIDC identity token attached to Pub/Sub push requests."""
    if not PUBSUB_PUSH_AUDIENCE or not PUBSUB_PUSH_SERVICE_ACCOUNT:
        raise HTTPException(
            status_code=503,
            detail="Pub/Sub authentication is not configured",
        )

    # Cloud Run may forward the platform authorization token here.
    authorization = (
        request.headers.get("X-Serverless-Authorization")
        or request.headers.get("Authorization")
        or ""
    )

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Missing Pub/Sub identity token",
        )

    try:
        claims = id_token.verify_oauth2_token(
            token,
            GoogleAuthRequest(),
            audience=PUBSUB_PUSH_AUDIENCE,
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Pub/Sub identity token",
        )

    if (
        claims.get("email") != PUBSUB_PUSH_SERVICE_ACCOUNT
        or claims.get("email_verified") is not True
    ):
        raise HTTPException(
            status_code=403,
            detail="Unexpected Pub/Sub service identity",
        )



@app.post("/gmail/webhook")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    verify_pubsub_push(request)

    print("\n" + "=" * 60)
    print("PUB/SUB NOTIFICATION RECEIVED")
    print("=" * 60)

    try:
        pubsub_data = await request.json()
    except Exception as error:
        print("Invalid JSON received:", error)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message = pubsub_data.get("message")
    if not message:
        return {"status": "ignored"}

    encoded_data = message.get("data")
    if not encoded_data:
        return {"status": "ignored"}

    notification = parse_pubsub_notification(encoded_data)
    if not notification:
        return {"status": "ignored"}

    new_history_id = notification.get("historyId")
    email_address = notification.get("emailAddress")
    if not new_history_id:
        return {"status": "ignored"}

    # Route by emailAddress if matching user exists in database
    target_user = None
    if email_address:
        clean_email = normalize_email(email_address)
        target_user = db.scalar(select(User).where(User.email == clean_email))

    if target_user:
        previous_history_id = target_user.gmail_history_id
        if not previous_history_id:
            target_user.gmail_history_id = str(new_history_id)
            db.commit()
            return {"status": "initialized", "user": target_user.email, "history_id": new_history_id}

        if str(previous_history_id) == str(new_history_id):
            return {"status": "duplicate", "user": target_user.email, "history_id": new_history_id}

        # Schedule async processing so Pub/Sub receives an instant HTTP 200 response
        background_tasks.add_task(
            background_process_user_history,
            target_user.id,
            previous_history_id,
            str(new_history_id),
        )
        return {"status": "accepted", "user": target_user.email, "history_id": new_history_id}
    else:
        # Fallback to single-owner file state
        previous_history_id = load_history_id()
        if not previous_history_id:
            save_history_id(new_history_id)
            return {"status": "initialized", "history_id": new_history_id}

        if str(previous_history_id) == str(new_history_id):
            return {"status": "duplicate", "history_id": new_history_id}

        background_tasks.add_task(
            background_process_fallback_history,
            previous_history_id,
            str(new_history_id),
        )
        return {"status": "accepted", "history_id": new_history_id}


# ==================================================
# Authentication Endpoints
# ==================================================

@app.post("/auth/register", response_model=TokenResponse)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    clean_email = normalize_email(request.email)
    existing_user = db.scalar(select(User).where(User.email == clean_email))
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email address is already registered",
        )

    pwd_hash = hash_password(request.password)
    default_name = clean_email.split("@")[0].capitalize()

    user = User(
        email=clean_email,
        password_hash=pwd_hash,
        name=default_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user)
    raw_refresh_token, _ = create_refresh_token(db, user.id)

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    clean_email = normalize_email(request.email)
    user = db.scalar(select(User).where(User.email == clean_email))

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled",
        )

    access_token = create_access_token(user)
    raw_refresh_token, _ = create_refresh_token(db, user.id)

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/google", response_model=TokenResponse)
def google_login(
    request: GoogleLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_token = request.get_token()
    if not raw_token:
        raise HTTPException(
            status_code=400,
            detail="Google credential token missing",
        )

    google_info = verify_google_token(raw_token)
    google_id = google_info.get("sub")
    email_raw = google_info.get("email", "")
    name = google_info.get("name", "")
    picture = google_info.get("picture")

    if not google_id or not email_raw:
        raise HTTPException(
            status_code=400,
            detail="Google ID token missing user email or ID",
        )

    clean_email = normalize_email(email_raw)

    user = db.scalar(select(User).where(User.google_id == google_id))
    if not user:
        user = db.scalar(select(User).where(User.email == clean_email))
        if user:
            user.google_id = google_id
            if picture and not user.picture:
                user.picture = picture
            if name and not user.name:
                user.name = name
            db.commit()

    if not user:
        user = User(
            google_id=google_id,
            email=clean_email,
            name=name or clean_email.split("@")[0].capitalize(),
            picture=picture,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if request.gmail_refresh_token:
        user.gmail_refresh_token = request.gmail_refresh_token
        db.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled",
        )

    access_token = create_access_token(user)
    raw_refresh_token, _ = create_refresh_token(db, user.id)

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


def exchange_google_code_for_tokens(code: str) -> dict:
    """Exchange OAuth authorization code with Google token endpoint."""
    import requests
    from gmail.gmail_service import get_client_credentials

    client_id, client_secret = get_client_credentials()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth client credentials not configured on server",
        )

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code",
        },
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth code exchange failed: {response.text}",
        )

    return response.json()


def _bg_setup_watch(user_id: int) -> None:
    """Background task: create/renew Gmail watch after login without blocking the response."""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            return
        try:
            setup_watch_for_user(user, db)
        except Exception as err:
            print(f"Warning: Automatic watch setup failed for {user.email}: {err}")


@app.post("/auth/google/code", response_model=TokenResponse)
def google_code_login(
    request: GoogleCodeRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    tokens = exchange_google_code_for_tokens(request.code)
    id_token_raw = tokens.get("id_token")
    gmail_refresh_token = tokens.get("refresh_token")

    if not id_token_raw:
        raise HTTPException(
            status_code=400,
            detail="Google authorization code did not return ID token",
        )

    google_info = verify_google_token(id_token_raw)
    google_id = google_info.get("sub")
    email_raw = google_info.get("email", "")
    name = google_info.get("name", "")
    picture = google_info.get("picture")

    if not google_id or not email_raw:
        raise HTTPException(
            status_code=400,
            detail="Google ID token missing user email or ID",
        )

    clean_email = normalize_email(email_raw)

    user = db.scalar(select(User).where(User.google_id == google_id))
    if not user:
        user = db.scalar(select(User).where(User.email == clean_email))
        if user:
            user.google_id = google_id
            if picture and not user.picture:
                user.picture = picture
            if name and not user.name:
                user.name = name
            db.commit()

    if not user:
        user = User(
            google_id=google_id,
            email=clean_email,
            name=name or clean_email.split("@")[0].capitalize(),
            picture=picture,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if gmail_refresh_token:
        user.gmail_refresh_token = gmail_refresh_token
        db.commit()

        # Run Gmail watch setup in background so login response is instant
        if os.getenv("GMAIL_PUBSUB_TOPIC"):
            background_tasks.add_task(_bg_setup_watch, user.id)

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled",
        )

    access_token = create_access_token(user)
    raw_refresh_token, _ = create_refresh_token(db, user.id)

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/connect-gmail")
def connect_gmail(
    background_tasks: BackgroundTasks,
    body: ConnectGmailTokenRequest | None = None,
    code: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_db(credentials, db)

    refresh_token = None
    if code:
        tokens = exchange_google_code_for_tokens(code)
        refresh_token = tokens.get("refresh_token")
    elif body and body.gmail_refresh_token:
        refresh_token = body.gmail_refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No Gmail refresh token or valid authorization code provided",
        )

    current_user.gmail_refresh_token = refresh_token
    db.commit()
    db.refresh(current_user)

    # Run watch setup in background so this endpoint returns instantly
    if os.getenv("GMAIL_PUBSUB_TOPIC"):
        background_tasks.add_task(_bg_setup_watch, current_user.id)

    return {
        "status": "connected",
        "email": current_user.email,
    }


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    raw_token = (
        (body.refresh_token if body and body.refresh_token else None)
        or request.cookies.get("refresh_token")
    )

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing",
        )

    new_raw_refresh, new_access, user = verify_and_rotate_refresh_token(
        db, raw_token
    )

    response.set_cookie(
        key="refresh_token",
        value=new_raw_refresh,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_raw_refresh,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    raw_token = (
        (body.refresh_token if body and body.refresh_token else None)
        or request.cookies.get("refresh_token")
    )

    if raw_token:
        revoke_refresh_token(db, raw_token)

    response.delete_cookie("refresh_token")

    return {"detail": "Successfully logged out"}


@app.get("/auth/me", response_model=UserResponse)
def get_me(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_db(credentials, db)
    return UserResponse.model_validate(current_user)


# ==================================================
# Protected User Data Endpoints
# ==================================================

@app.get("/emails", response_model=list[EmailResponse])
def get_emails(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    current_user = get_current_user_from_db(credentials, db)

    emails = (
        db.query(Email)
        .filter(Email.user_id == current_user.id)
        .order_by(Email.classified_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return emails


@app.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(
    email_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    current_user = get_current_user_from_db(credentials, db)

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id,
            Email.user_id == current_user.id,
        )
        .first()
    )

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    return email


@app.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    current_user = get_current_user_from_db(credentials, db)

    emails = (
        db.query(Email)
        .filter(Email.user_id == current_user.id)
        .all()
    )

    total = len(emails)
    by_category = {}
    by_priority = {}
    requires_response_count = 0

    for email in emails:
        raw_cat = (email.category or "Uncategorized").strip()
        cat = raw_cat.capitalize() if raw_cat else "Uncategorized"

        raw_prio = (email.priority or "Unassigned").strip()
        prio = raw_prio.capitalize() if raw_prio else "Unassigned"

        by_category[cat] = by_category.get(cat, 0) + 1
        by_priority[prio] = by_priority.get(prio, 0) + 1

        if email.requires_response:
            requires_response_count += 1

    return StatsResponse(
        total=total,
        total_emails=total,
        requires_response=requires_response_count,
        by_category=by_category,
        by_priority=by_priority,
        categories=by_category,
    )


@app.post("/gmail/watch")
def register_watch_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_db(credentials, db)
    res = setup_watch_for_user(current_user, db)
    return {
        "status": "success",
        "user": current_user.email,
        "history_id": current_user.gmail_history_id,
        "expiration": current_user.gmail_watch_expiration,
        "details": res,
    }


# ==================================================
# Cloud Scheduler: Renew all Gmail watches
# ==================================================

@app.post("/gmail/watch/renew-all")
def renew_all_watches(request: Request, db: Session = Depends(get_db)):
    """
    Renew Gmail push-notification watches for every active user.

    Intended to be called by Google Cloud Scheduler on a schedule
    (Gmail watches expire after ~7 days). Requires the
    ``X-Scheduler-Token`` header to match the ``SCHEDULER_SECRET``
    environment variable so the endpoint is not publicly exploitable.
    """
    

    scheduler_secret = os.getenv("SCHEDULER_SECRET")
    if not scheduler_secret:
        raise HTTPException(
            status_code=503,
            detail="Scheduler authentication is not configured",
    )

    incoming_token = request.headers.get("X-Scheduler-Token", "")
    if incoming_token != scheduler_secret:
        raise HTTPException(
            status_code=401,
            detail="Invalid scheduler token",
    )
    

    users = (
        db.query(User)
        .filter(User.is_active == True, User.gmail_refresh_token.isnot(None))
        .all()
    )

    results = []
    for user in users:
        try:
            res = setup_watch_for_user(user, db)
            results.append({"user": user.email, **res})
        except Exception as err:
            print(f"[renew-all] Failed to renew watch for {user.email}: {err}")
            results.append({"user": user.email, "status": "error", "detail": str(err)})

    return {"renewed": len(results), "results": results}
