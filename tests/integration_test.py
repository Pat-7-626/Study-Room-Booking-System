import pytest
import httpx
import uuid
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# --- Test Data ---
TEST_PASSWORD = "testpassword123"
ROOM_ID = f"TEST-ROOM-{uuid.uuid4().hex[:4]}"
MEMBER_EMAIL = f"member-{uuid.uuid4().hex[:4]}@test.com"
OTHER_MEMBER_EMAIL = f"other-{uuid.uuid4().hex[:4]}@test.com"
STAFF_EMAIL = f"staff-{uuid.uuid4().hex[:4]}@test.com"
ADMIN_EMAIL = f"admin-{uuid.uuid4().hex[:4]}@test.com"

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        yield c

def get_token(client, email, password, role="member"):
    # Try to register first (ignore if already exists)
    client.post("/register", json={"email": email, "password": password, "role": role})
    # Login to get token
    resp = client.post("/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}"
    return resp.json()["access_token"]

@pytest.fixture(scope="module")
def admin_token(client):
    return get_token(client, ADMIN_EMAIL, TEST_PASSWORD, "admin")

@pytest.fixture(scope="module")
def staff_token(client):
    return get_token(client, STAFF_EMAIL, TEST_PASSWORD, "staff")

@pytest.fixture(scope="module")
def member_token(client):
    return get_token(client, MEMBER_EMAIL, TEST_PASSWORD, "member")

@pytest.fixture(scope="module")
def other_member_token(client):
    return get_token(client, OTHER_MEMBER_EMAIL, TEST_PASSWORD, "member")

# --- 1. Authentication Tests ---
def test_auth_registration_and_login(client):
    email = f"auth-test-{uuid.uuid1()}@test.com"
    reg_resp = client.post("/register", json={"email": email, "password": TEST_PASSWORD, "role": "member"})
    assert reg_resp.status_code == 200
    
    login_resp = client.post("/login", json={"email": email, "password": TEST_PASSWORD})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

# --- 2. Room Management Tests (Staff/Admin) ---
def test_staff_can_manage_rooms(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Create room
    create_resp = client.post("/rooms", headers=headers, json={
        "room_id": ROOM_ID,
        "capacity": 4,
        "status": "Available"
    })
    assert create_resp.status_code == 200
    
    # Update room
    update_resp = client.put(f"/rooms/{ROOM_ID}", headers=headers, json={
        "room_id": ROOM_ID,
        "capacity": 5,
        "status": "Maintenance"
    })
    assert update_resp.status_code == 200
    
    # Verify update
    get_resp = client.get("/rooms")
    rooms = get_resp.json()
    room = next(r for r in rooms if r["room_id"] == ROOM_ID)
    assert room["capacity"] == 5
    assert room["status"] == "Maintenance"

def test_admin_can_manage_rooms(client, admin_token):
    # Setup - use unique ID to avoid conflict with staff test
    admin_room_id = f"ADMIN-RM-{uuid.uuid4().hex[:4]}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Admin Create
    resp = client.post("/rooms", headers=headers, json={"room_id": admin_room_id, "capacity": 10, "status": "Available"})
    assert resp.status_code == 200
    
    # Admin Delete
    del_resp = client.delete(f"/rooms/{admin_room_id}", headers=headers)
    assert del_resp.status_code == 200

def test_member_cannot_manage_rooms(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}
    resp = client.post("/rooms", headers=headers, json={"room_id": "HACK-ROOM", "capacity": 10})
    assert resp.status_code == 403 # Forbidden

# --- 3. Reservation Tests (Member / Admin) ---
def test_member_booking_flow(client, member_token, staff_token):
    # Ensure room is available first
    client.put(f"/rooms/{ROOM_ID}", headers={"Authorization": f"Bearer {staff_token}"}, json={
        "room_id": ROOM_ID, "capacity": 5, "status": "Available"
    })
    
    headers = {"Authorization": f"Bearer {member_token}"}
    tomorrow = datetime.now() + timedelta(days=1)
    start_ms = int(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, 0).timestamp() * 1000)
    end_ms = start_ms + (3600 * 1000)
    
    # 1. Create Reservation
    res_resp = client.post("/reserve", headers=headers, json={
        "room_id": ROOM_ID, "start": start_ms, "end": end_ms, "group_size": 2
    })
    assert res_resp.status_code == 200
    res_id = res_resp.json().get("res_id")
    
    # 2. View My Reservations
    my_resp = client.get("/my-reservations", headers=headers)
    assert any(r["room_id"] == ROOM_ID for r in my_resp.json())
    
    # 3. Cancel Own Reservation
    del_resp = client.delete(f"/reserve/{res_id}", headers=headers)
    assert del_resp.status_code == 200

def test_member_cannot_cancel_others_reservation(client, member_token, other_member_token, staff_token):
    # 1. Member A creates a reservation
    client.put(f"/rooms/{ROOM_ID}", headers={"Authorization": f"Bearer {staff_token}"}, json={
        "room_id": ROOM_ID, "capacity": 5, "status": "Available"
    })
    
    tomorrow = datetime.now() + timedelta(days=1)
    start_ms = int(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0, 0).timestamp() * 1000)
    end_ms = start_ms + (3600 * 1000)
    
    resp_a = client.post("/reserve", headers={"Authorization": f"Bearer {member_token}"}, json={
        "room_id": ROOM_ID, "start": start_ms, "end": end_ms, "group_size": 1
    })
    res_id = resp_a.json()["res_id"]
    
    # 2. Member B tries to delete Member A's reservation
    resp_b = client.delete(f"/reserve/{res_id}", headers={"Authorization": f"Bearer {other_member_token}"})
    assert resp_b.status_code == 404 # Backend returns 404 for 'not found or unauthorized'

def test_admin_can_manage_reservations(client, admin_token, member_token, staff_token):
    # 1. Member creates a reservation
    tomorrow = datetime.now() + timedelta(days=1)
    start_ms = int(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 11, 0, 0).timestamp() * 1000)
    end_ms = start_ms + (3600 * 1000)
    
    resp = client.post("/reserve", headers={"Authorization": f"Bearer {member_token}"}, json={
        "room_id": ROOM_ID, "start": start_ms, "end": end_ms, "group_size": 1
    })
    res_id = resp.json()["res_id"]
    
    # 2. Admin updates the reservation (e.g., changing group size)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    upd_resp = client.put(f"/reserve/{res_id}", headers=admin_headers, json={"group_size": 10})
    assert upd_resp.status_code == 200
    
    # 3. Admin deletes the reservation
    del_resp = client.delete(f"/reserve/{res_id}", headers=admin_headers)
    assert del_resp.status_code == 200

# --- 4. Conflict & Capacity Tests ---
def test_capacity_enforcement(client, member_token, staff_token):
    # Set room capacity to 2
    client.put(f"/rooms/{ROOM_ID}", headers={"Authorization": f"Bearer {staff_token}"}, json={
        "room_id": ROOM_ID, "capacity": 2, "status": "Available"
    })
    
    headers = {"Authorization": f"Bearer {member_token}"}
    tomorrow = datetime.now() + timedelta(days=2)
    start_ms = int(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 14, 0, 0).timestamp() * 1000)
    end_ms = start_ms + (3600 * 1000)
    
    # Book 1 spot
    client.post("/reserve", headers=headers, json={"room_id": ROOM_ID, "start": start_ms, "end": end_ms, "group_size": 1})
    
    # Try to book 2 spots (Total 3 > Capacity 2)
    fail_resp = client.post("/reserve", headers=headers, json={"room_id": ROOM_ID, "start": start_ms, "end": end_ms, "group_size": 2})
    assert fail_resp.status_code == 400
    assert "Not enough capacity" in fail_resp.json()["detail"]

# --- 5. User Management Tests (Admin) ---
def test_admin_can_manage_users(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    list_resp = client.get("/users", headers=headers)
    assert list_resp.status_code == 200
    
    # Update role
    update_resp = client.put(f"/users/{MEMBER_EMAIL}", headers=headers, json={"role": "staff"})
    assert update_resp.status_code == 200
    
def test_staff_cannot_manage_users(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/users", headers=headers)
    assert resp.status_code == 403

# --- 6. Staff/Admin Record Oversight ---
def test_staff_can_view_all_reservations(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/all-reservations", headers=headers)
    assert resp.status_code == 200

def test_member_cannot_view_all_reservations(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}
    resp = client.get("/all-reservations", headers=headers)
    assert resp.status_code == 403
