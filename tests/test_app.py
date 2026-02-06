"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_activity():
    """Return a sample activity name"""
    return "Chess Club"


@pytest.fixture
def sample_email():
    """Return a sample student email"""
    return "test@mergington.edu"


class TestActivitiesEndpoint:
    """Tests for the /activities GET endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_contains_expected_fields(self, client):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup POST endpoint"""
    
    def test_signup_successful(self, client, sample_activity, sample_email):
        """Test successful signup for an activity"""
        response = client.post(
            f"/activities/{sample_activity}/signup?email={sample_email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
    
    def test_signup_adds_participant(self, client, sample_activity, sample_email):
        """Test that signup adds participant to the activity"""
        # Get initial participants
        response = client.get("/activities")
        initial_participants = response.json()[sample_activity]["participants"].copy()
        
        # Signup with new email
        new_email = "new_student@mergington.edu"
        client.post(f"/activities/{sample_activity}/signup?email={new_email}")
        
        # Check participant was added
        response = client.get("/activities")
        updated_participants = response.json()[sample_activity]["participants"]
        assert new_email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1
    
    def test_signup_duplicate_fails(self, client, sample_activity, sample_email):
        """Test that signing up twice with same email fails"""
        # First signup
        client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        
        # Try duplicate signup
        response = client.post(
            f"/activities/{sample_activity}/signup?email={sample_email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, sample_email):
        """Test that signing up for non-existent activity fails"""
        response = client.post(
            f"/activities/Nonexistent Activity/signup?email={sample_email}"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister DELETE endpoint"""
    
    def test_unregister_successful(self, client, sample_activity):
        """Test successful unregistration from an activity"""
        # First signup
        test_email = "unregister_test@mergington.edu"
        client.post(f"/activities/{sample_activity}/signup?email={test_email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/{sample_activity}/unregister?email={test_email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]
    
    def test_unregister_removes_participant(self, client, sample_activity):
        """Test that unregister removes participant from activity"""
        # Signup
        test_email = "remove_test@mergington.edu"
        client.post(f"/activities/{sample_activity}/signup?email={test_email}")
        
        # Get participants before unregister
        response = client.get("/activities")
        participants_before = response.json()[sample_activity]["participants"].copy()
        assert test_email in participants_before
        
        # Unregister
        client.delete(f"/activities/{sample_activity}/unregister?email={test_email}")
        
        # Check participant was removed
        response = client.get("/activities")
        participants_after = response.json()[sample_activity]["participants"]
        assert test_email not in participants_after
        assert len(participants_after) == len(participants_before) - 1
    
    def test_unregister_not_registered_fails(self, client, sample_activity):
        """Test that unregistering a non-registered student fails"""
        response = client.delete(
            f"/activities/{sample_activity}/unregister?email=not_registered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails"""
        response = client.delete(
            f"/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestRootEndpoint:
    """Tests for the / GET endpoint"""
    
    def test_root_redirects(self, client):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
