"""Tests for resources."""

import json


def test_server_status_resource():
    """Test server status resource."""
    from app.resources.server_info import get_server_status

    status_str = get_server_status()
    status = json.loads(status_str)

    assert "server_name" in status
    assert "version" in status
    assert "status" in status
    assert status["status"] == "running"
    assert "features" in status
    assert len(status["features"]) > 0


def test_models_list_resource():
    """Test models list resource."""
    from app.resources.server_info import get_models_list

    models_str = get_models_list()
    models = json.loads(models_str)

    assert "supported_models" in models
    assert len(models["supported_models"]) > 0

    # Check first model structure
    first_model = models["supported_models"][0]
    assert "id" in first_model
    assert "full_id" in first_model
    assert "capabilities" in first_model


def test_api_docs_resource():
    """Test API documentation resource."""
    from app.resources.server_info import get_api_docs

    docs = get_api_docs()

    assert isinstance(docs, str)
    assert len(docs) > 0
    assert "Overview" in docs
    assert "create_video_task" in docs
    assert "get_video_task" in docs
    assert "Example Usage" in docs
