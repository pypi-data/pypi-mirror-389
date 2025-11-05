"""
Tests for {{project_name}} FastAPI application

This module contains tests for the main FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)


class TestBasicEndpoints:
    """Test basic application endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "{{project_name}}" in data["message"]
        assert "version" in data

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "debug" in data


class TestItemsCRUD:
    """Test CRUD operations for items."""

    def test_get_empty_items_list(self):
        """Test getting items when none exist."""
        response = client.get("/items")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_item(self):
        """Test creating a new item."""
        item_data = {
            "name": "Test Item",
            "description": "A test item",
            "price": 29.99
        }
        response = client.post("/items", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == item_data["name"]
        assert data["description"] == item_data["description"]
        assert data["price"] == item_data["price"]
        assert "id" in data
        assert data["is_active"] is True

    def test_create_item_validation_error(self):
        """Test creating item with invalid data."""
        # Test negative price
        item_data = {
            "name": "Invalid Item",
            "description": "Invalid price",
            "price": -10.0
        }
        response = client.post("/items", json=item_data)
        assert response.status_code == 422

        # Test empty name
        item_data = {
            "name": "",
            "description": "Empty name",
            "price": 10.0
        }
        response = client.post("/items", json=item_data)
        assert response.status_code == 422

    def test_get_item_by_id(self):
        """Test getting a specific item by ID."""
        # First create an item
        item_data = {
            "name": "Get Test Item",
            "description": "Item for get test",
            "price": 15.50
        }
        create_response = client.post("/items", json=item_data)
        assert create_response.status_code == 201
        created_item = create_response.json()
        item_id = created_item["id"]

        # Now get the item
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == item_data["name"]

    def test_get_nonexistent_item(self):
        """Test getting an item that doesn't exist."""
        response = client.get("/items/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_item(self):
        """Test updating an existing item."""
        # First create an item
        item_data = {
            "name": "Update Test Item",
            "description": "Item for update test",
            "price": 20.00
        }
        create_response = client.post("/items", json=item_data)
        created_item = create_response.json()
        item_id = created_item["id"]

        # Update the item
        update_data = {
            "name": "Updated Item",
            "description": "Updated description",
            "price": 25.00
        }
        response = client.put(f"/items/{item_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["price"] == update_data["price"]

    def test_update_nonexistent_item(self):
        """Test updating an item that doesn't exist."""
        update_data = {
            "name": "Nonexistent Item",
            "description": "This won't work",
            "price": 10.00
        }
        response = client.put("/items/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_item(self):
        """Test deleting an item."""
        # First create an item
        item_data = {
            "name": "Delete Test Item",
            "description": "Item for delete test",
            "price": 5.00
        }
        create_response = client.post("/items", json=item_data)
        created_item = create_response.json()
        item_id = created_item["id"]

        # Delete the item
        response = client.delete(f"/items/{item_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_item(self):
        """Test deleting an item that doesn't exist."""
        response = client.delete("/items/99999")
        assert response.status_code == 404

    def test_get_all_items_after_operations(self):
        """Test getting all items after creating several."""
        # Create multiple items
        items_data = [
            {"name": "Item 1", "description": "First item", "price": 10.00},
            {"name": "Item 2", "description": "Second item", "price": 20.00},
            {"name": "Item 3", "description": "Third item", "price": 30.00},
        ]
        
        created_ids = []
        for item_data in items_data:
            response = client.post("/items", json=item_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # Get all items
        response = client.get("/items")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= len(items_data)  # May have items from other tests
        
        # Check that our created items are in the response
        item_names = [item["name"] for item in items]
        for item_data in items_data:
            assert item_data["name"] in item_names


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    def test_invalid_http_method(self):
        """Test using invalid HTTP method."""
        response = client.patch("/items")  # PATCH not supported
        assert response.status_code == 405