from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)

    yield

    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    request_path = "/"

    # Act
    response = client.get(request_path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    # Arrange
    request_path = "/activities"

    # Act
    response = client.get(request_path)

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_for_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_duplicate_participant_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_for_full_activity_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "new-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_unregister_participant_removes_email():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_missing_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found in this activity"}
