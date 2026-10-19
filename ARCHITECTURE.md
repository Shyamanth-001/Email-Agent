# System Architecture & Technical Documentation

This document explains the technical architecture, database design, core features, and automated workflows of the **AI Email Classifier & Multi-User Gmail Dashboard**.

---

## 🏛️ High-Level System Architecture

```
┌───────────────────────────────┐
│     React Frontend (Vite)     │
│   (Dashboard, Charts, OAuth)  │
└──────────────┬────────────────┘
               │ HTTP REST APIs / Bearer JWT
               ▼
┌───────────────────────────────┐        ┌─────────────────────────────┐
│    FastAPI Backend (Python)   │ <----> │ PostgreSQL Database         │
│   (Auth, Webhooks, Watch)     │        │ (Users, Emails, Tokens)     │
└──────┬────────────────┬───────┘        └─────────────────────────────┘
       │                │
       │ Google OAuth   │ Push Notifications
       ▼                ▼
┌──────────────┐ ┌──────────────────────┐ ┌────────────────────────────┐
│  Google API  │ │ GCP Cloud Pub/Sub    │ │ Groq LLM API               │
│ (Gmail Read) │ │ Webhook Notifications│ │ (Email Classification)     │
└──────────────┘ └──────────────────────┘ └────────────────────────────┘
```

---

## 🗄️ Database Schema & Data Models

The system uses **PostgreSQL** via **SQLAlchemy ORM** to enforce strict per-user data isolation.

### 1. `users` Table (`api/models.py`)

Stores user identity, authentication credentials, and per-user Gmail OAuth state.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `Integer` (PK) | Unique user identifier. |
| `email` | `String` (Unique, Indexed) | User email address. |
| `hashed_password` | `String` (Nullable) | Password hash (if password auth is used). |
| `name` | `String` | User full name from Google profile. |
| `picture` | `String` (Nullable) | User profile avatar URL. |
| `gmail_refresh_token` | `Text` (Nullable) | Encrypted Google OAuth refresh token for background Gmail API access. |
| `gmail_history_id` | `String` (Nullable) | History ID pointer for incremental Gmail synchronization. |
| `gmail_watch_expiration` | `DateTime` (Nullable) | Expiration timestamp of active Gmail Pub/Sub watch subscription. |
| `is_active` | `Boolean` | User status flag. |
| `created_at` | `DateTime` | User account creation timestamp. |

---

### 2. `emails` Table (`api/models.py`)

Stores classified emails mapped directly to their owner (`user_id`).

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `Integer` (PK) | Local message database ID. |
| `gmail_message_id` | `String` (Indexed) | Google Gmail API message ID. |
| `gmail_thread_id` | `String` (Nullable) | Google Gmail API thread ID. |
| `user_id` | `Integer` (FK -> `users.id`) | Owner ID enforcing multi-user data isolation. |
| `sender` | `String` | Sender name and email address. |
| `subject` | `String` | Email subject header. |
| `body` | `Text` | Plain text contents of the email. |
| `received_at` | `DateTime` | Header date when email was sent/received. |
| `category` | `String` | AI Category (`Important`, `Work`, `Personal`, `Promotions`, `Spam`, `General`). |
| `priority` | `String` | AI Urgency Priority (`High`, `Medium`, `Low`). |
| `sentiment` | `String` | AI Sentiment analysis (`Positive`, `Neutral`, `Negative / Frustrated`). |
| `summary` | `Text` | LLM generated bulleted summary. |
| `requires_response` | `Boolean` | Flag indicating whether response or action is required. |
| `classified_at` | `DateTime` | Timestamp of AI classification. |

---

## ⚡ Key System Features & Automated Logic

### 1. Unified Google OAuth Authentication Flow

- **Single Sign-In Action**: The user clicks **"Sign in with Google"** on the React frontend.
- **Scope Request**: Opens the Google OAuth 2.0 popup requesting:
  - Identity: `userinfo.email`, `userinfo.profile`
  - Gmail Access: `https://www.googleapis.com/auth/gmail.readonly`
- **Code Exchange (`POST /auth/google/code`)**:
  - The frontend receives an authorization `code` and sends it to FastAPI.
  - FastAPI exchanges the `code` with Google OAuth servers using `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
  - Captures the user's `gmail_refresh_token` and saves it to PostgreSQL.
  - Issues a secure JWT access token to authenticate frontend API calls.
  - **Triggers Immediate Watch**: Calls `setup_watch_for_user(user, db)` immediately after login.

---

### 2. Automated Gmail Watch Subscription Management

No manual commands (`--watch`) are required:

1. **FastAPI Startup Trigger (`@app.on_event("startup")`)**:
   - When the backend starts (`uvicorn api.main:app`), it automatically queries all active database users with a `gmail_refresh_token`.
   - Executes `setup_all_user_watches()`, registering push notifications for all users with Google Cloud Pub/Sub.
2. **On-Demand User Watch Setup**:
   - Whenever a new user signs in or connects their account, the backend registers their Gmail watch instantly.

---

### 3. Real-Time GCP Pub/Sub Push Webhook Processing

```
New Email Arrives in User Inbox
       │
       ▼
Google Pub/Sub Topic Push Notification
       │
       ▼
POST /gmail/webhook (FastAPI Endpoint)
       │
       ├─► Decodes base64 notification (Extracts email address & historyId)
       ├─► Queries PostgreSQL for User by email address
       ├─► Obtains user's stored `gmail_refresh_token`
       ├─► Calls `get_added_message_ids()` using Gmail History API
       ├─► Fetches message body for new email IDs
       ├─► Sends text to Groq LLM for AI Classification & Sentiment Analysis
       └─► Saves classified results into `emails` table linked to `user_id`
```

---

### 4. AI Email Classification Pipeline (`llm/classifier.py`)

When a new message arrives, the LLM prompt evaluates:

- **Category**: Classifies into `Work`, `Important`, `Personal`, `Financial`, `Promotions`, `Spam`, or `General`.
- **Priority**: Determines urgency level (`High`, `Medium`, `Low`).
- **Sentiment**: Detects tone (`Positive`, `Neutral`, `Negative / Frustrated`).
- **Action Required**: Evaluates if the sender requires a follow-up or reply.
- **Summary**: Generates a concise summary of key points.

---

### 5. Multi-User Isolation & Security

- All API endpoints (`/emails`, `/stats`, `/emails/{id}`) require a valid Bearer JWT.
- Database queries enforce `.filter(Email.user_id == current_user.id)`.
- Prevents cross-tenant data leaks; each user can only view their own emails and dashboard analytics.

---

### 6. Frontend Dashboard & Visualization (`frontend/`)

- **Real-Time Overview**: Displays total processed emails, high-priority counts, required responses, and frustrated sentiment alerts.
- **Interactive Charts**:
  - **Emails by Category**: Distribution bar chart powered by Recharts.
  - **Emails by Priority**: Donut pie chart breaking down urgency.
- **Email Table & Search**: Searchable, paginated table with category badges, priority tags, and email detail drawer.

---

## 🛠️ Environment Configuration (`.env`)

```env
# Backend Database Connection
DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost:5432/email_agent

# JWT Authentication Secret
JWT_SECRET=YOUR_SECURE_JWT_SECRET_KEY

# Google OAuth 2.0 Credentials (Must match Google Cloud Console)
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-YOUR_GOOGLE_CLIENT_SECRET

# Google Cloud Pub/Sub Topic
GMAIL_PUBSUB_TOPIC=projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC_NAME

# LLM API Key (Groq)
GROQ_API_KEY=gsk_YOUR_GROQ_API_KEY
```

---

## 🚀 Execution Commands

1. **Start Backend Server**:
   ```powershell
   .venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
   ```

2. **Start Frontend App**:
   ```powershell
   npm run dev
   ```

3. **Expose Public Webhook Tunnel (for Pub/Sub)**:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
