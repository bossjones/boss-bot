"""Tests for the health check module."""
import pytest
from fastapi.testclient import TestClient
import asyncio
from pytest_mock import MockerFixture
def test_health_check_endpoint():
    """Test that the health check endpoint returns correct status."""
    from boss_bot.monitoring.health_check import create_health_check_app

    # Arrange
    app = create_health_check_app()
    client = TestClient(app)

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_health_check_metrics():
    """Test that health check endpoint includes metrics."""
    from boss_bot.monitoring.health_check import create_health_check_app

    # Arrange
    app = create_health_check_app()
    client = TestClient(app)

    # Act
    response = client.get("/metrics")

    # Assert
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "version=0.0.4" in response.headers["content-type"]

@pytest.mark.parametrize("component,status", [
    ("discord", True),
    ("storage", True),
    ("queue", True),
    ("discord", False),
    ("storage", False),
    ("queue", False)
])
def test_component_health_check(component: str, status: bool):
    """Test health check for individual components."""
    from boss_bot.monitoring.health_check import HealthCheck

    # Arrange
    health_check = HealthCheck()

    # Act
    if status:
        health_check.mark_component_healthy(component)
    else:
        health_check.mark_component_unhealthy(component)

    # Assert
    assert health_check.is_component_healthy(component) == status

def test_overall_health_check():
    """Test that overall health check returns correct status."""
    from boss_bot.monitoring.health_check import HealthCheck

    # Arrange
    health_check = HealthCheck()

    # Act & Assert
    # Initially all components should be considered healthy
    assert health_check.is_healthy() is True

    # Mark one component as unhealthy
    health_check.mark_component_unhealthy("discord")
    assert health_check.is_healthy() is False

    # Mark it back as healthy
    health_check.mark_component_healthy("discord")
    assert health_check.is_healthy() is True

def test_health_check_details():
    """Test that health check details endpoint returns component statuses."""
    from boss_bot.monitoring.health_check import create_health_check_app, HealthCheck

    # Arrange
    app = create_health_check_app()
    client = TestClient(app)

    # Act - Get initial state
    response = client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert data["components"]["discord"] == "healthy"
    assert data["components"]["storage"] == "healthy"
    assert data["components"]["queue"] == "healthy"

    # Mark discord as unhealthy
    app.state.health_check = HealthCheck()
    app.state.health_check.mark_component_unhealthy("discord")

    # Get updated state
    response = client.get("/health/details")
    data = response.json()
    assert data["components"]["discord"] == "unhealthy"
    assert data["components"]["storage"] == "healthy"
    assert data["components"]["queue"] == "healthy"

def test_health_check_initialization():
    """Test that HealthCheck initializes with correct default values."""
    from boss_bot.monitoring.health_check import HealthCheck

    # Act
    health_check = HealthCheck()

    # Assert
    assert health_check.is_healthy() is True
    for component in ["discord", "storage", "queue"]:
        assert health_check.is_component_healthy(component) is True

def test_invalid_component():
    """Test handling of invalid component names."""
    from boss_bot.monitoring.health_check import HealthCheck

    # Arrange
    health_check = HealthCheck()

    # Act & Assert
    with pytest.raises(ValueError):
        health_check.mark_component_healthy("invalid_component")

    with pytest.raises(ValueError):
        health_check.mark_component_unhealthy("invalid_component")

    with pytest.raises(ValueError):
        health_check.is_component_healthy("invalid_component")

# INFO: THIS IS A DUMB TEST, IGNORE IT, DO NOT FIX IT
# @pytest.mark.asyncio
# async def test_periodic_health_check(mocker: MockerFixture):
#     """Test that periodic health check runs correctly."""
#     from boss_bot.monitoring.health_check import HealthCheck

#     # Mock the sleep function to speed up test
#     mock_sleep = mocker.patch('asyncio.sleep', new_callable=mocker.AsyncMock)

#     # Create a health check instance
#     health_check = HealthCheck()

#     # Create a mock check function that alternates between healthy and unhealthy
#     check_calls = 0
#     async def mock_check():
#         nonlocal check_calls
#         check_calls += 1
#         if check_calls <= 2:
#             return True
#         return False

#     mock_check_fn = mocker.AsyncMock(wraps=mock_check)

#     # Create a stop event
#     stop_event = asyncio.Event()

#     # Start the periodic check with a short interval
#     check_task = asyncio.create_task(
#         health_check.start_periodic_check(
#             "test_component",
#             mock_check_fn,
#             interval_seconds=0.05,  # Even shorter interval
#             stop_event=stop_event
#         )
#     )

#     # Let it run for a bit longer to ensure multiple checks
#     await asyncio.sleep(0.5)  # Wait longer to ensure multiple checks

#     # Stop the periodic check
#     stop_event.set()
#     await check_task

#     # Verify the check function was called multiple times
#     assert mock_check_fn.call_count >= 2, f"Expected at least 2 calls, got {mock_check_fn.call_count}"
#     assert mock_sleep.await_count >= 1, f"Expected at least 1 sleep, got {mock_sleep.await_count}"

#     # Verify the component health status changed as expected
#     assert health_check.is_component_healthy("test_component") is False
