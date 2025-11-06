import json
import pytest
from unittest.mock import MagicMock, patch

# ----------------------------------------------------
# --- GET /api/restaurants Tests ---
# ----------------------------------------------------


def test_get_restaurants(client, mocker):
    """
    Test the GET /api/restaurants endpoint with multiple restaurants.
    """
    import restaurantRoutes

    mock_data = [
        {"id": "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1", "name": "The Rustic Olive"},
        {"id": "b2b2b2b2-b2b2-b2b2-b2b2-b2b2b2b2b2b2", "name": "The Daily Grind"},
    ]

    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 200
    assert response.json == mock_data
    restaurantRoutes.supabase.table.assert_called_with("restaurants")
    mock_chain.select.assert_called_with("*")
    mock_chain.select.return_value.execute.assert_called_once()


def test_get_restaurants_single_restaurant(client, mocker):
    """
    Test GET /api/restaurants with only one restaurant in database.
    """
    import restaurantRoutes

    mock_data = [
        {
            "id": "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1",
            "name": "Solo Restaurant",
            "address": "123 Alone St",
        }
    ]

    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["name"] == "Solo Restaurant"


def test_get_restaurants_404_not_found(client, mocker):
    """
    Test the GET /api/restaurants endpoint when no restaurants are found (empty list).
    """
    import restaurantRoutes

    mock_response = MagicMock()
    mock_response.data = []

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 404
    assert response.json == {"error": "No restaurants found"}


def test_get_restaurants_none_data(client, mocker):
    """
    Test GET /api/restaurants when response.data is None.
    """
    import restaurantRoutes

    mock_response = MagicMock()
    mock_response.data = None

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 404
    assert response.json == {"error": "No restaurants found"}


def test_get_restaurants_500_server_error(client, mocker):
    """
    Test GET /api/restaurants for 500 error when database fails.
    """
    import restaurantRoutes

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.side_effect = Exception(
        "Simulated database connection error"
    )

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 500
    data = response.get_json()
    assert data["error"] == "Simulated database connection error"


def test_get_restaurants_database_timeout(client, mocker):
    """
    Test GET /api/restaurants with database timeout exception.
    """
    import restaurantRoutes

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.side_effect = Exception("Connection timeout")

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get("/api/restaurants")

    assert response.status_code == 500
    assert "Connection timeout" in response.get_json()["error"]


# ----------------------------------------------------
# --- GET /api/restaurant/<id> Tests ---
# ----------------------------------------------------


def test_get_restaurant_details(client, mocker):
    """
    Test the GET /api/restaurant/<id> endpoint for a successful fetch.
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
    mock_data_dict = {
        "id": mock_restaurant_id,
        "name": "The Rustic Olive",
        "address": "123 Main St, Raleigh, NC",
        "menu_items": [{"id": "m1m1m1", "name": "Margherita Pizza", "price": 14.50}],
    }

    mock_response = MagicMock()
    mock_response.data = [mock_data_dict]

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 200
    assert response.json == mock_data_dict
    restaurantRoutes.supabase.table.assert_called_with("restaurants")
    mock_chain.select.assert_called_with("*, menu_items(*)")
    mock_chain.select.return_value.eq.assert_called_with("id", mock_restaurant_id)
    mock_chain.select.return_value.eq.return_value.execute.assert_called_once()


def test_get_restaurant_details_with_multiple_menu_items(client, mocker):
    """
    Test GET /api/restaurant/<id> with multiple menu items.
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
    mock_data_dict = {
        "id": mock_restaurant_id,
        "name": "The Rustic Olive",
        "address": "123 Main St",
        "menu_items": [
            {"id": "m1", "name": "Pizza", "price": 14.50, "category": "Main"},
            {"id": "m2", "name": "Pasta", "price": 12.99, "category": "Main"},
            {"id": "m3", "name": "Salad", "price": 8.99, "category": "Appetizer"},
        ],
    }

    mock_response = MagicMock()
    mock_response.data = [mock_data_dict]

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 200
    assert len(response.json["menu_items"]) == 3
    assert response.json["menu_items"][0]["name"] == "Pizza"


def test_get_restaurant_details_no_menu_items(client, mocker):
    """
    Test GET /api/restaurant/<id> with no menu items.
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
    mock_data_dict = {
        "id": mock_restaurant_id,
        "name": "Empty Restaurant",
        "address": "123 Main St",
        "menu_items": [],
    }

    mock_response = MagicMock()
    mock_response.data = [mock_data_dict]

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 200
    assert response.json["menu_items"] == []


def test_get_restaurant_details_404_not_found(client, mocker):
    """
    Test the GET /api/restaurant/<id> endpoint when the ID does not exist.
    """
    import restaurantRoutes

    mock_restaurant_id = "00000000-0000-0000-0000-000000000000"

    mock_response = MagicMock()
    mock_response.data = []

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 404
    data = response.get_json()
    assert data == {"error": "Restaurant not found"}


def test_get_restaurant_details_none_data(client, mocker):
    """
    Test GET /api/restaurant/<id> when response.data is None.
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"

    mock_response = MagicMock()
    mock_response.data = None

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.return_value = mock_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Restaurant not found"}


def test_get_restaurant_details_invalid_uuid(client):
    """
    Test GET /api/restaurant/<id> with invalid UUID format.
    """
    response = client.get("/api/restaurant/not-a-valid-uuid")

    # Flask will return 404 for invalid UUID in route
    assert response.status_code == 404


def test_get_restaurant_details_500_error(client, mocker):
    """
    Test GET /api/restaurant/<id> for 500 error when database fails.
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"

    mock_chain = MagicMock()
    mock_chain.select.return_value.eq.return_value.execute.side_effect = Exception(
        "Database error"
    )

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.get(f"/api/restaurant/{mock_restaurant_id}")

    assert response.status_code == 500
    assert "Database error" in response.get_json()["error"]


# ----------------------------------------------------
# --- POST /api/restaurants Tests ---
# ----------------------------------------------------


def test_create_restaurant(client, mocker):
    """
    Test the POST /api/restaurants endpoint with menu items.
    """
    new_restaurant_payload = {
        "name": "The Test Spot",
        "address": "999 Test Ave",
        "banner_image_url": "/banners/test.png",
        "menu_items": [{"name": "Test Dish 1", "price": 10.99, "category": "Test"}],
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "t1t1t1t1-t1t1-t1t1-t1t1-t1t1t1t1t1t1",
            "name": "The Test Spot",
            "address": "999 Test Ave",
            "banner_image_url": "/banners/test.png",
        }
    ]

    mock_menu_response = MagicMock()
    mock_menu_response.data = [
        {
            "id": "m1m1m1m1-m1m1-m1m1-m1m1-m1m1m1m1m1m1",
            "name": "Test Dish 1",
            "price": 10.99,
            "category": "Test",
            "restaurant_id": "t1t1t1t1-t1t1-t1t1-t1t1-t1t1t1t1t1t1",
        }
    ]

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.side_effect = [
        mock_restaurant_response,
        mock_menu_response,
    ]
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 201
    assert response.json["name"] == "The Test Spot"
    assert response.json["id"] == "t1t1t1t1-t1t1-t1t1-t1t1-t1t1t1t1t1t1"
    assert len(response.json["menu_items"]) == 1
    assert response.json["menu_items"][0]["name"] == "Test Dish 1"


def test_create_restaurant_without_menu_items(client, mocker):
    """
    Test POST /api/restaurants without menu items.
    """
    new_restaurant_payload = {
        "name": "Simple Restaurant",
        "address": "100 Simple St",
        "banner_image_url": "/banners/simple.png",
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "s1s1s1s1-s1s1-s1s1-s1s1-s1s1s1s1s1s1",
            "name": "Simple Restaurant",
            "address": "100 Simple St",
            "banner_image_url": "/banners/simple.png",
        }
    ]

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.return_value = mock_restaurant_response
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 201
    assert response.json["name"] == "Simple Restaurant"
    assert response.json["menu_items"] == []


def test_create_restaurant_with_empty_menu_items_array(client, mocker):
    """
    Test POST /api/restaurants with empty menu_items array.
    """
    new_restaurant_payload = {
        "name": "Empty Menu Restaurant",
        "address": "200 Empty St",
        "menu_items": [],
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "e1e1e1e1-e1e1-e1e1-e1e1-e1e1e1e1e1e1",
            "name": "Empty Menu Restaurant",
            "address": "200 Empty St",
            "banner_image_url": None,
        }
    ]

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.return_value = mock_restaurant_response
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 201
    assert response.json["menu_items"] == []


def test_create_restaurant_with_multiple_menu_items(client, mocker):
    """
    Test POST /api/restaurants with multiple menu items.
    """
    new_restaurant_payload = {
        "name": "Full Menu Restaurant",
        "address": "300 Full St",
        "menu_items": [
            {"name": "Dish 1", "price": 10.99, "category": "Main"},
            {"name": "Dish 2", "price": 12.99, "category": "Main"},
            {"name": "Dish 3", "price": 5.99, "category": "Appetizer"},
        ],
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1",
            "name": "Full Menu Restaurant",
            "address": "300 Full St",
            "banner_image_url": None,
        }
    ]

    mock_menu_response = MagicMock()
    mock_menu_response.data = [
        {
            "id": "m1",
            "name": "Dish 1",
            "price": 10.99,
            "category": "Main",
            "restaurant_id": "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1",
        },
        {
            "id": "m2",
            "name": "Dish 2",
            "price": 12.99,
            "category": "Main",
            "restaurant_id": "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1",
        },
        {
            "id": "m3",
            "name": "Dish 3",
            "price": 5.99,
            "category": "Appetizer",
            "restaurant_id": "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1",
        },
    ]

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.side_effect = [
        mock_restaurant_response,
        mock_menu_response,
    ]
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 201
    assert len(response.json["menu_items"]) == 3


def test_create_restaurant_missing_name(client):
    """
    Test POST /api/restaurants with missing name (Bad Request 400).
    """
    response = client.post(
        "/api/restaurants", json={"address": "123 Test St", "menu_items": []}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Restaurant name is required"}


def test_create_restaurant_empty_name(client):
    """
    Test POST /api/restaurants with empty string name (Bad Request 400).
    """
    response = client.post(
        "/api/restaurants", json={"name": "", "address": "123 Test St"}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Restaurant name is required"}


def test_create_restaurant_null_name(client):
    """
    Test POST /api/restaurants with null name (Bad Request 400).
    """
    response = client.post(
        "/api/restaurants", json={"name": None, "address": "123 Test St"}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Restaurant name is required"}


def test_create_restaurant_no_json_body(client):
    """
    Test POST /api/restaurants with no JSON body.
    Flask may return 500 if get_json() is called on empty body.
    """
    response = client.post("/api/restaurants")

    # May be 400 or 500 depending on Flask error handling
    assert response.status_code in [400, 500]


def test_create_restaurant_empty_json_body(client):
    """
    Test POST /api/restaurants with empty JSON object (Bad Request 400).
    """
    response = client.post("/api/restaurants", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Restaurant name is required"}


def test_create_restaurant_fails_no_data(client, mocker):
    """
    Test POST /api/restaurants when restaurant creation returns no data (Error 500).
    """
    new_restaurant_payload = {
        "name": "Failed Restaurant",
        "address": "404 Fail St",
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = []
    mock_restaurant_response.error = "Insert failed"

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.return_value = mock_restaurant_response
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 500
    assert "Failed to create restaurant" in response.get_json()["error"]


def test_create_restaurant_fails_none_data(client, mocker):
    """
    Test POST /api/restaurants when restaurant creation returns None (Error 500).
    """
    new_restaurant_payload = {
        "name": "Failed Restaurant",
        "address": "404 Fail St",
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = None
    mock_restaurant_response.error = None

    mock_table_chain = MagicMock()
    mock_table_chain.insert.return_value.execute.return_value = mock_restaurant_response
    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_table_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 500
    assert "Failed to create restaurant" in response.get_json()["error"]


def test_create_restaurant_menu_items_fail_rollback(client, mocker):
    """
    Test POST /api/restaurants when menu items fail and restaurant gets rolled back.
    """
    new_restaurant_payload = {
        "name": "Rollback Restaurant",
        "address": "500 Rollback St",
        "menu_items": [{"name": "Bad Item", "price": 9.99}],
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "r1r1r1r1-r1r1-r1r1-r1r1-r1r1r1r1r1r1",
            "name": "Rollback Restaurant",
            "address": "500 Rollback St",
        }
    ]

    mock_menu_response = MagicMock()
    mock_menu_response.data = []  # Menu insert fails

    mock_delete_response = MagicMock()
    mock_delete_response.data = [{"id": "r1r1r1r1-r1r1-r1r1-r1r1-r1r1r1r1r1r1"}]

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.execute.return_value = (
        mock_delete_response
    )

    call_count = [0]

    def table_side_effect(table_name):
        call_count[0] += 1
        if call_count[0] == 1:  # restaurants insert
            chain = MagicMock()
            chain.insert.return_value.execute.return_value = mock_restaurant_response
            return chain
        elif call_count[0] == 2:  # menu_items insert
            chain = MagicMock()
            chain.insert.return_value.execute.return_value = mock_menu_response
            return chain
        else:  # restaurants delete (rollback)
            return mock_delete_chain

    mocker.patch("restaurantRoutes.supabase.table", side_effect=table_side_effect)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 500
    assert "Menu items failed to save" in response.get_json()["error"]
    # Verify delete was called for rollback
    mock_delete_chain.delete.assert_called()


def test_create_restaurant_exception_rollback(client, mocker):
    """
    Test POST /api/restaurants when an exception occurs and rollback is triggered.
    """
    new_restaurant_payload = {
        "name": "Exception Restaurant",
        "address": "600 Exception St",
        "menu_items": [{"name": "Item", "price": 10.99}],
    }

    mock_restaurant_response = MagicMock()
    mock_restaurant_response.data = [
        {
            "id": "x1x1x1x1-x1x1-x1x1-x1x1-x1x1x1x1x1x1",
            "name": "Exception Restaurant",
            "address": "600 Exception St",
        }
    ]

    mock_delete_response = MagicMock()
    mock_delete_response.data = [{"id": "x1x1x1x1-x1x1-x1x1-x1x1-x1x1x1x1x1x1"}]

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.execute.return_value = (
        mock_delete_response
    )

    call_count = [0]

    def table_side_effect(table_name):
        call_count[0] += 1
        if call_count[0] == 1:  # restaurants insert
            chain = MagicMock()
            chain.insert.return_value.execute.return_value = mock_restaurant_response
            return chain
        elif call_count[0] == 2:  # menu_items insert - throws exception
            chain = MagicMock()
            chain.insert.return_value.execute.side_effect = Exception(
                "Unexpected error"
            )
            return chain
        else:  # restaurants delete (rollback)
            return mock_delete_chain

    mocker.patch("restaurantRoutes.supabase.table", side_effect=table_side_effect)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 500
    assert "Unexpected error" in response.get_json()["error"]


def test_create_restaurant_exception_no_rollback_needed(client, mocker):
    """
    Test POST /api/restaurants when exception occurs before restaurant creation.
    """
    new_restaurant_payload = {
        "name": "Early Fail Restaurant",
        "address": "700 Early St",
    }

    mock_chain = MagicMock()
    mock_chain.insert.return_value.execute.side_effect = Exception(
        "Early database error"
    )

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.post("/api/restaurants", json=new_restaurant_payload)

    assert response.status_code == 500
    assert "Early database error" in response.get_json()["error"]


# ----------------------------------------------------
# --- POST /api/recommendations Tests ---
# ----------------------------------------------------


def test_get_recommendations_success(client, mocker):
    """
    Test POST /api/recommendations with successful AI response.
    """
    import restaurantRoutes

    request_payload = {"mood": "happy and hungry"}

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Happy Burgers",
            "menu_items": [{"id": "m1", "name": "Cheeseburger", "price": 8.99}],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    mock_ai_recommendations = [
        {"restaurant_id": "r1", "reason": "Great mood-boosting food"}
    ]
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        return_value=mock_ai_recommendations,
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 200
    assert response.json == {"recommendations": mock_ai_recommendations}


def test_get_recommendations_missing_mood(client):
    """
    Test POST /api/recommendations with missing mood (Bad Request 400).
    """
    response = client.post("/api/recommendations", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Mood text is required"}


def test_get_recommendations_empty_mood(client):
    """
    Test POST /api/recommendations with empty mood string (Bad Request 400).
    """
    response = client.post("/api/recommendations", json={"mood": ""})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Mood text is required"}


def test_get_recommendations_null_mood(client):
    """
    Test POST /api/recommendations with null mood (Bad Request 400).
    """
    response = client.post("/api/recommendations", json={"mood": None})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Mood text is required"}


def test_get_recommendations_no_restaurants(client, mocker):
    """
    Test POST /api/recommendations when no restaurants in database (404).
    """
    request_payload = {"mood": "happy"}

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = []

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 404
    assert response.get_json() == {"error": "No restaurants available in database"}


def test_get_recommendations_none_restaurants(client, mocker):
    """
    Test POST /api/recommendations when restaurants data is None (404).
    """
    request_payload = {"mood": "happy"}

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = None

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 404
    assert response.get_json() == {"error": "No restaurants available in database"}


def test_get_recommendations_ai_service_exception(client, mocker):
    """
    Test POST /api/recommendations when AI service throws exception (500).
    """
    request_payload = {"mood": "happy"}

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Test Restaurant",
            "menu_items": [{"id": "m1", "name": "Item", "price": 9.99}],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        side_effect=Exception("AI service failed"),
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 500
    assert "AI service failed" in response.get_json()["error"]


def test_get_recommendations_json_decode_error(client, mocker):
    """
    Test POST /api/recommendations when AI service returns invalid JSON (500).
    """
    import json as json_module

    request_payload = {"mood": "happy"}

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Test Restaurant",
            "menu_items": [],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        side_effect=json_module.JSONDecodeError("Invalid JSON", "doc", 0),
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 500
    assert "Failed to parse AI response" in response.get_json()["error"]


def test_get_recommendations_database_error(client, mocker):
    """
    Test POST /api/recommendations when database query fails (500).
    """
    request_payload = {"mood": "happy"}

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.side_effect = Exception(
        "Database connection lost"
    )

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 500
    assert "Database connection lost" in response.get_json()["error"]


def test_get_recommendations_no_json_body(client):
    """
    Test POST /api/recommendations with no JSON body.
    """
    response = client.post("/api/recommendations")

    # May be 400 or 500 depending on Flask error handling
    assert response.status_code in [400, 500]


def test_get_recommendations_with_special_characters(client, mocker):
    """
    Test POST /api/recommendations with special characters in mood.
    """
    import restaurantRoutes

    request_payload = {"mood": "I'm feeling 😊 happy & excited!!!"}

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Happy Place",
            "menu_items": [{"id": "m1", "name": "Joy Burger", "price": 10.99}],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    mock_ai_recommendations = [{"restaurant_id": "r1", "reason": "Matches your mood"}]
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        return_value=mock_ai_recommendations,
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 200
    assert response.json == {"recommendations": mock_ai_recommendations}


def test_get_recommendations_very_long_mood(client, mocker):
    """
    Test POST /api/recommendations with very long mood text.
    """
    import restaurantRoutes

    request_payload = {"mood": "happy " * 100}  # Very long mood text

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Restaurant",
            "menu_items": [],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    mock_ai_recommendations = []
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        return_value=mock_ai_recommendations,
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 200
    assert response.json == {"recommendations": []}


def test_get_recommendations_empty_result(client, mocker):
    """
    Test POST /api/recommendations when AI returns empty recommendations.
    """
    import restaurantRoutes

    request_payload = {"mood": "neutral"}

    mock_restaurants_data = [
        {
            "id": "r1",
            "name": "Restaurant",
            "menu_items": [],
        }
    ]

    mock_restaurants_response = MagicMock()
    mock_restaurants_response.data = mock_restaurants_data

    mock_chain = MagicMock()
    mock_chain.select.return_value.execute.return_value = mock_restaurants_response

    mocker.patch("restaurantRoutes.supabase.table", return_value=mock_chain)

    mock_ai_recommendations = []
    mocker.patch(
        "restaurantRoutes.ai_service.get_ai_recommendations",
        return_value=mock_ai_recommendations,
    )

    response = client.post("/api/recommendations", json=request_payload)

    assert response.status_code == 200
    assert response.json == {"recommendations": []}


# ----------------------------------------------------
# --- Integration-style Tests ---
# ----------------------------------------------------


def test_get_all_then_get_single_restaurant(client, mocker):
    """
    Test getting all restaurants then getting a single one (integration-style).
    """
    import restaurantRoutes

    mock_restaurant_id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"

    # Mock for GET all
    mock_all_response = MagicMock()
    mock_all_response.data = [
        {"id": mock_restaurant_id, "name": "Restaurant 1"},
        {"id": "b2b2b2b2-b2b2-b2b2-b2b2-b2b2b2b2b2b2", "name": "Restaurant 2"},
    ]

    # Mock for GET single
    mock_single_response = MagicMock()
    mock_single_response.data = [
        {
            "id": mock_restaurant_id,
            "name": "Restaurant 1",
            "address": "123 Main St",
            "menu_items": [{"id": "m1", "name": "Pizza", "price": 12.99}],
        }
    ]

    call_count = [0]

    def table_side_effect(table_name):
        call_count[0] += 1
        if call_count[0] == 1:  # GET all
            chain = MagicMock()
            chain.select.return_value.execute.return_value = mock_all_response
            return chain
        else:  # GET single
            chain = MagicMock()
            chain.select.return_value.eq.return_value.execute.return_value = (
                mock_single_response
            )
            return chain

    mocker.patch("restaurantRoutes.supabase.table", side_effect=table_side_effect)

    # Get all restaurants
    all_response = client.get("/api/restaurants")
    assert all_response.status_code == 200
    assert len(all_response.json) == 2

    # Get single restaurant
    single_response = client.get(f"/api/restaurant/{mock_restaurant_id}")
    assert single_response.status_code == 200
    assert single_response.json["name"] == "Restaurant 1"
    assert len(single_response.json["menu_items"]) == 1
