"""
Tests for the Mergington High School Activities API
"""

import copy
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import app, activities as original_activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities dict to its original state after each test."""
    backup = copy.deepcopy(original_activities)
    yield
    original_activities.clear()
    original_activities.update(backup)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict_of_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        for activity in response.json().values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        email = "newstudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        activities_response = client.get("/activities").json()
        assert email in activities_response["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self, client):
        email = "duplicate@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        response = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        # michael is pre-seeded in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/signup", params={"email": email})
        activities_response = client.get("/activities").json()
        assert email not in activities_response["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_participant_not_signed_up_returns_400(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
