import os
# Force DATABASE_URL to SQLite for all unit tests to avoid connecting to Postgres
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from unittest.mock import MagicMock
import app.cache

# Mock Redis to prevent tests from trying to connect to a local Redis server
mock_redis = MagicMock()
mock_redis.scan_iter.return_value = []
mock_redis.get.return_value = None  # Cache miss by default
app.cache.redis_client = mock_redis

# Use an in-memory SQLite DB for tests — no Postgres needed
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_task():
    response = client.post("/tasks", json={"title": "Test task", "description": "Testing"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test task"
    assert data["completed"] is False

def test_list_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_task():
    create = client.post("/tasks", json={"title": "Get me"})
    task_id = create.json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id

def test_update_task():
    create = client.post("/tasks", json={"title": "Update me"})
    task_id = create.json()["id"]
    response = client.put(f"/tasks/{task_id}", json={"completed": True})
    assert response.status_code == 200
    assert response.json()["completed"] is True

def test_delete_task():
    create = client.post("/tasks", json={"title": "Delete me"})
    task_id = create.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    # Verify it's gone
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404

def test_task_not_found():
    response = client.get("/tasks/99999")
    assert response.status_code == 404