"""Tests for the health check module."""
import pytest
from fastapi.testclient import TestClient

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
    assert "prometheus" in response.headers["content-type"]

@pytest.mark.parametrize("component,status", [
    ("discord", True),
    ("storage", True),
    ("queue", True),
    ("discord", False),
    ("storage", False),
    ("queue", False)
])
def test_component_health_check(component, status):
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
    health_check = HealthCheck()

    # Act
    health_check.mark_component_unhealthy("discord")
    response = client.get("/health/details")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert data["components"]["discord"] == "unhealthy"
    assert data["components"]["storage"] == "healthy"
    assert data["components"]["queue"] == "healthy"

@pytest.mark.asyncio
async def test_periodic_health_check(mocker):
    """Test that periodic health check runs correctly."""
    from boss_bot.monitoring.health_check import HealthCheck

    # Arrange
    health_check = HealthCheck()
    mock_check_fn = mocker.Mock(return_value=True)
    mocker.patch('asyncio.sleep', return_value=None)

    # Act
    await health_check.start_periodic_check("test_component", mock_check_fn, interval_seconds=1)

    # Assert
    mock_check_fn.assert_called_once()
    assert health_check.is_component_healthy("test_component") is True

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
