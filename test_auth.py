import sys
import os
from datetime import datetime, timezone, timedelta

TEST_DB_FILE = "./test_auth_db.sqlite"
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["JWT_SECRET"] = "test-secret-key-1234567890"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id.apps.googleusercontent.com"
os.environ["OWNER_EMAIL"] = "owner@example.com"

sys.path.append(".")

from database import engine, Base, init_database
init_database()

from fastapi.testclient import TestClient
from api.main import app
from models import User, Email, RefreshToken
import jwt

client = TestClient(app)

def test_full_auth_flow():
    print("\n==========================================")
    print("RUNNING AUTH & AUTHORIZATION TEST SUITE")
    print("==========================================")

    # 1. Register User 1
    reg_res = client.post("/auth/register", json={
        "email": "user1@example.com",
        "password": "Password123!"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    user1_data = reg_res.json()
    assert "access_token" in user1_data
    assert "refresh_token" in user1_data
    assert user1_data["user"]["email"] == "user1@example.com"
    user1_id = user1_data["user"]["id"]
    token1 = user1_data["access_token"]
    refresh1 = user1_data["refresh_token"]
    print("1. New user registration PASSED")

    # 2. Reject duplicate registration
    dup_res = client.post("/auth/register", json={
        "email": "user1@example.com",
        "password": "AnotherPassword123!"
    })
    assert dup_res.status_code == 400, f"Duplicate registration check failed: {dup_res.text}"
    print("2. Duplicate registration rejection PASSED")

    # 3. Login with valid password
    login_res = client.post("/auth/login", json={
        "email": "user1@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    assert "access_token" in login_res.json()
    print("3. User login PASSED")

    # 4. Reject invalid login credentials with generic error
    bad_login = client.post("/auth/login", json={
        "email": "user1@example.com",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Invalid email or password"
    print("4. Generic 401 invalid credentials PASSED")

    # 5. /auth/me returns current user
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "user1@example.com"
    print("5. /auth/me endpoint PASSED")

    # 6. Unauthenticated /emails returns 401 or 403
    unauth_emails = client.get("/emails")
    assert unauth_emails.status_code in (401, 403)
    print("6. Unauthenticated API protection PASSED")

    # 7. Register User 2
    reg2 = client.post("/auth/register", json={
        "email": "user2@example.com",
        "password": "Password123!"
    })
    assert reg2.status_code == 200
    token2 = reg2.json()["access_token"]
    user2_id = reg2.json()["user"]["id"]

    # Insert test emails directly into DB for User 1 and User 2
    from database import SessionLocal
    with SessionLocal() as db:
        email_u1 = Email(
            gmail_message_id="msg_u1_1",
            user_id=user1_id,
            sender="boss@corp.com",
            subject="User 1 Confidential",
            body="Secret text for user 1",
            category="Work",
            priority="High",
            sentiment="Neutral",
            summary="Work email",
            requires_response=True
        )
        email_u2 = Email(
            gmail_message_id="msg_u2_1",
            user_id=user2_id,
            sender="friend@other.com",
            subject="User 2 Personal",
            body="Personal text for user 2",
            category="Personal",
            priority="Low",
            sentiment="Positive",
            summary="Personal email",
            requires_response=False
        )
        db.add_all([email_u1, email_u2])
        db.commit()
        email_u1_id = email_u1.id
        email_u2_id = email_u2.id

    # 8. User 1 accesses User 1 emails
    u1_emails = client.get("/emails", headers={"Authorization": f"Bearer {token1}"})
    assert u1_emails.status_code == 200
    assert len(u1_emails.json()) == 1
    assert u1_emails.json()[0]["id"] == email_u1_id
    print("7. User data isolation (User 1 emails) PASSED")

    # 9. User 1 CANNOT access User 2 email
    cross_access = client.get(f"/emails/{email_u2_id}", headers={"Authorization": f"Bearer {token1}"})
    assert cross_access.status_code == 404
    print("8. User authorization boundary (User 1 cannot access User 2 email) PASSED")

    # 10. User stats isolation
    stats1 = client.get("/stats", headers={"Authorization": f"Bearer {token1}"})
    assert stats1.status_code == 200
    assert stats1.json()["total"] == 1
    assert stats1.json()["categories"] == {"Work": 1}

    stats2 = client.get("/stats", headers={"Authorization": f"Bearer {token2}"})
    assert stats2.status_code == 200
    assert stats2.json()["total"] == 1
    assert stats2.json()["categories"] == {"Personal": 1}
    print("9. User stats isolation PASSED")

    # 11. Refresh token rotation
    ref_res = client.post("/auth/refresh", json={"refresh_token": refresh1})
    assert ref_res.status_code == 200, f"Refresh failed: {ref_res.text}"
    ref_data = ref_res.json()
    new_token1 = ref_data["access_token"]
    new_refresh1 = ref_data["refresh_token"]
    assert new_token1 != token1
    assert new_refresh1 != refresh1
    print("10. Refresh token rotation PASSED")

    # 12. Refreshing again with new refresh token works
    ref_res2 = client.post("/auth/refresh", json={"refresh_token": new_refresh1})
    assert ref_res2.status_code == 200
    new_refresh2 = ref_res2.json()["refresh_token"]
    print("11. Subsequent refresh token rotation PASSED")

    # 13. Reuse of revoked/old refresh token causes token family revocation!
    reuse_res = client.post("/auth/refresh", json={"refresh_token": refresh1})
    assert reuse_res.status_code == 401
    assert "reuse detected" in reuse_res.json()["detail"].lower()

    # Verify that current active token in family is now ALSO revoked due to reuse detection
    family_test = client.post("/auth/refresh", json={"refresh_token": new_refresh2})
    assert family_test.status_code == 401
    print("12. Refresh token reuse detection & token family revocation PASSED")

    # 14. Logout revokes token
    login_fresh = client.post("/auth/login", json={
        "email": "user1@example.com",
        "password": "Password123!"
    })
    fresh_refresh = login_fresh.json()["refresh_token"]

    logout_res = client.post("/auth/logout", json={"refresh_token": fresh_refresh})
    assert logout_res.status_code == 200

    # 15. Logged out refresh token cannot be refreshed
    logout_ref = client.post("/auth/refresh", json={"refresh_token": fresh_refresh})
    assert logout_ref.status_code == 401
    print("13. Logout & server-side refresh token revocation PASSED")

    # 17. Multi-user identical Gmail message ID isolation
    from repository import save_classified_email
    from ai.schemas import EmailClassification
    dummy_classification = EmailClassification(
        category="general",
        priority="low",
        sentiment="neutral",
        summary="Test email",
        requires_response=False
    )
    with SessionLocal() as db:
        e1, c1 = save_classified_email(
            db,
            gmail_message_id="shared_msg_999",
            gmail_thread_id="thread_999",
            sender="news@test.com",
            subject="Newsletter",
            body="Content",
            received_at=None,
            classification=dummy_classification,
            user_id=user1_id,
        )
        e2, c2 = save_classified_email(
            db,
            gmail_message_id="shared_msg_999",
            gmail_thread_id="thread_999",
            sender="news@test.com",
            subject="Newsletter",
            body="Content",
            received_at=None,
            classification=dummy_classification,
            user_id=user2_id,
        )
        assert c1 is True
        assert c2 is True
        assert e1.user_id == user1_id
        assert e2.user_id == user2_id
    print("15. Multi-user identical Gmail message ID isolation PASSED")

    print("\nALL 15 AUTOMATED INTEGRATION TESTS SUCCEEDED!")

if __name__ == "__main__":
    test_full_auth_flow()

