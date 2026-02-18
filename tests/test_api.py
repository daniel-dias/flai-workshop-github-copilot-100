"""
Test cases for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
    activities["Soccer Team"]["participants"] = ["alex@mergington.edu", "sarah@mergington.edu"]
    activities["Swimming Club"]["participants"] = ["james@mergington.edu", "emily@mergington.edu"]
    activities["Drama Club"]["participants"] = ["lily@mergington.edu", "noah@mergington.edu"]
    activities["Art Studio"]["participants"] = ["ava@mergington.edu", "mason@mergington.edu"]
    activities["Debate Team"]["participants"] = ["isabella@mergington.edu", "ethan@mergington.edu"]
    activities["Science Club"]["participants"] = ["mia@mergington.edu", "lucas@mergington.edu"]
    yield


class TestRootEndpoint:
    """Test cases for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test cases for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_includes_correct_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_has_initial_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successfully(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds the participant"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert "test@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_registration(self, client):
        """Test that duplicate registration is prevented"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newcoder@mergington.edu"
        )
        assert response.status_code == 200
        assert "newcoder@mergington.edu" in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successfully(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister actually removes the participant"""
        initial_count = len(activities["Chess Club"]["participants"])
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_non_registered_participant(self, client):
        """Test unregistering a participant who isn't registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_with_url_encoded_activity_name(self, client):
        """Test unregister with URL-encoded activity name"""
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=emma@mergington.edu"
        )
        assert response.status_code == 200
        assert "emma@mergington.edu" not in activities["Programming Class"]["participants"]


class TestIntegrationScenarios:
    """Integration test scenarios"""

    def test_full_signup_and_unregister_flow(self, client):
        """Test complete flow: get activities, signup, verify, unregister, verify"""
        email = "integration@mergington.edu"
        activity = "Chess Club"
        
        # Get initial state
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"]
        assert email not in initial_participants
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        participants_after_signup = response.json()[activity]["participants"]
        assert email in participants_after_signup
        assert len(participants_after_signup) == len(initial_participants) + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        final_participants = response.json()[activity]["participants"]
        assert email not in final_participants
        assert len(final_participants) == len(initial_participants)

    def test_multiple_signups_different_activities(self, client):
        """Test signing up for multiple different activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Chess Club", "Programming Class", "Science Club"]
        
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all signups
        response = client.get("/activities")
        data = response.json()
        
        for activity in activities_to_join:
            assert email in data[activity]["participants"]

    def test_activity_capacity_tracking(self, client):
        """Test that participant count is tracked correctly"""
        activity = "Chess Club"
        
        # Get initial state
        response = client.get("/activities")
        data = response.json()
        max_participants = data[activity]["max_participants"]
        initial_count = len(data[activity]["participants"])
        initial_spots_left = max_participants - initial_count
        
        # Add a participant
        client.post(f"/activities/{activity}/signup?email=newbie@mergington.edu")
        
        # Verify count changed
        response = client.get("/activities")
        data = response.json()
        new_count = len(data[activity]["participants"])
        new_spots_left = max_participants - new_count
        
        assert new_count == initial_count + 1
        assert new_spots_left == initial_spots_left - 1
