import pytest
import json
from unittest.mock import MagicMock

# --- Fixtures (from conftest.py) ---
# We assume conftest.py provides 'client' and 'mocker'

# ----------------------------------------------------
# --- Shopping Cart Routes (cartRoutes.py) Tests ---
# ----------------------------------------------------


@pytest.fixture
def cart_payload():
    """A reusable payload for cart tests."""
    return {
        "user_id": "8a8a8a8a-8a8a-8a8a-8a8a-8a8a8a8a8a8a",
        "menu_item_id": "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1",
        "quantity": 1,
    }


# ----------------------------------------------------
# --- POST /api/cart (Add to Cart) Tests ---
# ----------------------------------------------------


def test_add_to_cart_success(client, mocker, cart_payload):
    """
    Test POST /api/cart (Success 201)
    """
    import cartRoutes

    mock_response_data = {
        "id": "c1c1c1",
        "user_id": cart_payload["user_id"],
        "menu_item_id": cart_payload["menu_item_id"],
        "quantity": 1,
    }
    mock_response = MagicMock()
    mock_response.data = [mock_response_data]

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=cart_payload)

    assert response.status_code == 201
    assert response.json == mock_response_data
    mock_upsert_chain.upsert.assert_called_with(
        cart_payload, on_conflict="user_id, menu_item_id"
    )


def test_add_to_cart_with_custom_quantity(client, mocker, cart_payload):
    """
    Test POST /api/cart with custom quantity (Success 201)
    """
    import cartRoutes

    custom_payload = cart_payload.copy()
    custom_payload["quantity"] = 5

    mock_response_data = {
        "id": "c1c1c1",
        "user_id": custom_payload["user_id"],
        "menu_item_id": custom_payload["menu_item_id"],
        "quantity": 5,
    }
    mock_response = MagicMock()
    mock_response.data = [mock_response_data]

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=custom_payload)

    assert response.status_code == 201
    assert response.json["quantity"] == 5


def test_add_to_cart_missing_user_id(client, cart_payload):
    """
    Test POST /api/cart with missing user_id (Bad Request 400)
    """
    payload = cart_payload.copy()
    del payload["user_id"]

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id and menu_item_id are required"}


def test_add_to_cart_missing_menu_item_id(client, cart_payload):
    """
    Test POST /api/cart with missing menu_item_id (Bad Request 400)
    """
    payload = cart_payload.copy()
    del payload["menu_item_id"]

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id and menu_item_id are required"}


def test_add_to_cart_both_ids_missing(client):
    """
    Test POST /api/cart with both IDs missing (Bad Request 400)
    """
    response = client.post("/api/cart", json={"quantity": 2})

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id and menu_item_id are required"}


def test_add_to_cart_empty_user_id(client, cart_payload):
    """
    Test POST /api/cart with empty string user_id (Bad Request 400)
    """
    payload = cart_payload.copy()
    payload["user_id"] = ""

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id and menu_item_id are required"}


def test_add_to_cart_empty_menu_item_id(client, cart_payload):
    """
    Test POST /api/cart with empty string menu_item_id (Bad Request 400)
    """
    payload = cart_payload.copy()
    payload["menu_item_id"] = ""

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id and menu_item_id are required"}


def test_add_to_cart_quantity_zero_triggers_delete(client, mocker, cart_payload):
    """
    Test POST /api/cart with quantity 0 triggers removal (Success 204)
    """
    import cartRoutes

    payload = cart_payload.copy()
    payload["quantity"] = 0

    mock_response = MagicMock()
    mock_response.data = [{"id": "c1c1c1"}]  # Item was deleted

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 204
    # Verify delete was called
    mock_delete_chain.delete.assert_called()


def test_add_to_cart_negative_quantity_triggers_delete(client, mocker, cart_payload):
    """
    Test POST /api/cart with negative quantity triggers removal (Success 204)
    """
    import cartRoutes

    payload = cart_payload.copy()
    payload["quantity"] = -5

    mock_response = MagicMock()
    mock_response.data = [{"id": "c1c1c1"}]

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 204


def test_add_to_cart_quantity_zero_item_not_found(client, mocker, cart_payload):
    """
    Test POST /api/cart with quantity 0 but item doesn't exist (404)
    """
    import cartRoutes

    payload = cart_payload.copy()
    payload["quantity"] = 0

    mock_response = MagicMock()
    mock_response.data = []  # Nothing was deleted

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Item not found in cart"}


def test_add_to_cart_upsert_fails_no_data(client, mocker, cart_payload):
    """
    Test POST /api/cart when upsert returns no data (Error 500)
    """
    import cartRoutes

    mock_response = MagicMock()
    mock_response.data = []  # Empty response

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=cart_payload)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Failed to update cart"}


def test_add_to_cart_upsert_fails_none_data(client, mocker, cart_payload):
    """
    Test POST /api/cart when upsert returns None (Error 500)
    """
    import cartRoutes

    mock_response = MagicMock()
    mock_response.data = None

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=cart_payload)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Failed to update cart"}


def test_add_to_cart_exception_handling(client, mocker, cart_payload):
    """
    Test POST /api/cart exception handling (Error 500)
    """
    import cartRoutes

    mocker.patch(
        "cartRoutes.supabase.table",
        side_effect=Exception("Database connection error"),
    )

    response = client.post("/api/cart", json=cart_payload)

    assert response.status_code == 500
    assert "Database connection error" in response.get_json()["error"]


def test_add_to_cart_no_json_body(client):
    """
    Test POST /api/cart with no JSON body
    """
    response = client.post("/api/cart")

    assert response.status_code in [400, 500]  # Depends on Flask error handling


def test_add_to_cart_default_quantity(client, mocker, cart_payload):
    """
    Test POST /api/cart without quantity defaults to 1
    """
    import cartRoutes

    payload = cart_payload.copy()
    del payload["quantity"]  # Remove quantity

    mock_response_data = {
        "id": "c1c1c1",
        "user_id": payload["user_id"],
        "menu_item_id": payload["menu_item_id"],
        "quantity": 1,
    }
    mock_response = MagicMock()
    mock_response.data = [mock_response_data]

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=payload)

    assert response.status_code == 201
    # Verify upsert was called with quantity defaulting to 1
    call_args = mock_upsert_chain.upsert.call_args[0][0]
    assert call_args["quantity"] == 1


# ----------------------------------------------------
# --- GET /api/cart (Get Cart) Tests ---
# ----------------------------------------------------


def test_get_cart_success(client, mocker, cart_payload):
    """
    Test GET /api/cart (Success 200)
    """
    mock_data = [
        {
            "id": "c1c1c1",
            "quantity": 1,
            "menu_items": {
                "id": cart_payload["menu_item_id"],
                "name": "Pizza",
                "price": 10.99,
                "image_url": "https://example.com/pizza.jpg",
                "restaurant_id": "r1r1r1r1-r1r1-r1r1-r1r1-r1r1r1r1r1r1",
            },
        }
    ]
    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_select_chain = MagicMock()
    mock_select_chain.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_select_chain)

    response = client.get(f"/api/cart?user_id={cart_payload['user_id']}")

    assert response.status_code == 200
    assert response.json == mock_data
    mock_select_chain.select.return_value.eq.assert_called_with(
        "user_id", cart_payload["user_id"]
    )


def test_get_cart_multiple_items(client, mocker, cart_payload):
    """
    Test GET /api/cart with multiple items (Success 200)
    """
    mock_data = [
        {
            "id": "c1c1c1",
            "quantity": 2,
            "menu_items": {
                "id": "item1",
                "name": "Pizza",
                "price": 10.99,
                "image_url": "https://example.com/pizza.jpg",
                "restaurant_id": "r1",
            },
        },
        {
            "id": "c2c2c2",
            "quantity": 3,
            "menu_items": {
                "id": "item2",
                "name": "Burger",
                "price": 8.99,
                "image_url": "https://example.com/burger.jpg",
                "restaurant_id": "r1",
            },
        },
    ]
    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_select_chain = MagicMock()
    mock_select_chain.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_select_chain)

    response = client.get(f"/api/cart?user_id={cart_payload['user_id']}")

    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json == mock_data


def test_get_cart_empty(client, mocker, cart_payload):
    """
    Test GET /api/cart (Success 200, empty)
    """
    mock_response = MagicMock()
    mock_response.data = []  # Empty cart

    mock_select_chain = MagicMock()
    mock_select_chain.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_select_chain)

    response = client.get(f"/api/cart?user_id={cart_payload['user_id']}")

    assert response.status_code == 200
    assert response.json == []


def test_get_cart_missing_user_id(client):
    """
    Test GET /api/cart without user_id parameter (Bad Request 400)
    """
    response = client.get("/api/cart")

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id query parameter is required"}


def test_get_cart_empty_user_id(client):
    """
    Test GET /api/cart with empty user_id parameter (Bad Request 400)
    """
    response = client.get("/api/cart?user_id=")

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id query parameter is required"}


def test_get_cart_exception_handling(client, mocker, cart_payload):
    """
    Test GET /api/cart exception handling (Error 500)
    """
    import cartRoutes

    mocker.patch(
        "cartRoutes.supabase.table",
        side_effect=Exception("Database timeout"),
    )

    response = client.get(f"/api/cart?user_id={cart_payload['user_id']}")

    assert response.status_code == 500
    assert "Database timeout" in response.get_json()["error"]


# ----------------------------------------------------
# --- DELETE /api/cart/items/<id> (Remove from Cart) Tests ---
# ----------------------------------------------------


def test_remove_from_cart_success(client, mocker, cart_payload):
    """
    Test DELETE /api/cart/items/<id> (Success 204)
    """
    import cartRoutes

    mock_response = MagicMock()
    mock_response.data = [{"id": "c1c1c1"}]  # Supabase returns the deleted item

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={cart_payload['user_id']}"
    response = client.delete(url)

    assert response.status_code == 204

    # Assert the FIRST .eq() call
    first_eq_call = mock_delete_chain.delete.return_value.eq
    first_eq_call.assert_called_with("user_id", cart_payload["user_id"])

    # Assert the SECOND .eq() call
    second_eq_call = first_eq_call.return_value.eq
    second_eq_call.assert_called_with("menu_item_id", cart_payload["menu_item_id"])


def test_remove_from_cart_404(client, mocker, cart_payload):
    """
    Test DELETE /api/cart/items/<id> (Not Found 404)
    """
    mock_response = MagicMock()
    mock_response.data = []  # Nothing was deleted

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={cart_payload['user_id']}"
    response = client.delete(url)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Item not found in cart"}


def test_remove_from_cart_none_data(client, mocker, cart_payload):
    """
    Test DELETE /api/cart/items/<id> when data is None (Not Found 404)
    """
    mock_response = MagicMock()
    mock_response.data = None

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={cart_payload['user_id']}"
    response = client.delete(url)

    assert response.status_code == 404


def test_remove_from_cart_missing_user_id(client, cart_payload):
    """
    Test DELETE /api/cart/items/<id> without user_id parameter (Bad Request 400)
    """
    url = f"/api/cart/items/{cart_payload['menu_item_id']}"
    response = client.delete(url)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id query parameter is required"}


def test_remove_from_cart_empty_user_id(client, cart_payload):
    """
    Test DELETE /api/cart/items/<id> with empty user_id (Bad Request 400)
    """
    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id="
    response = client.delete(url)

    assert response.status_code == 400
    assert response.get_json() == {"error": "user_id query parameter is required"}


def test_remove_from_cart_exception_handling(client, mocker, cart_payload):
    """
    Test DELETE /api/cart/items/<id> exception handling (Error 500)
    """
    import cartRoutes

    mocker.patch(
        "cartRoutes.supabase.table",
        side_effect=Exception("Network error"),
    )

    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={cart_payload['user_id']}"
    response = client.delete(url)

    assert response.status_code == 500
    assert "Network error" in response.get_json()["error"]


def test_remove_from_cart_invalid_uuid_format(client, cart_payload):
    """
    Test DELETE /api/cart/items/<id> with invalid UUID format
    """
    url = f"/api/cart/items/not-a-valid-uuid?user_id={cart_payload['user_id']}"
    response = client.delete(url)

    # Flask will return 404 for invalid UUID in route
    assert response.status_code == 404


def test_remove_from_cart_different_user(client, mocker, cart_payload):
    """
    Test DELETE /api/cart/items/<id> with different user_id (Not Found 404)
    This simulates trying to delete another user's cart item
    """
    mock_response = MagicMock()
    mock_response.data = []  # Nothing deleted because wrong user

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_response
    )

    mocker.patch("cartRoutes.supabase.table", return_value=mock_delete_chain)

    different_user_id = "9b9b9b9b-9b9b-9b9b-9b9b-9b9b9b9b9b9b"
    url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={different_user_id}"
    response = client.delete(url)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Item not found in cart"}


# ----------------------------------------------------
# --- Integration-style Tests ---
# ----------------------------------------------------


def test_add_then_get_cart_flow(client, mocker, cart_payload):
    """
    Test adding an item then getting the cart (integration-style)
    """
    import cartRoutes

    # Mock for POST
    mock_post_response = MagicMock()
    mock_post_response.data = [
        {
            "id": "c1c1c1",
            "user_id": cart_payload["user_id"],
            "menu_item_id": cart_payload["menu_item_id"],
            "quantity": 1,
        }
    ]

    mock_post_chain = MagicMock()
    mock_post_chain.upsert.return_value.execute.return_value = mock_post_response

    # Mock for GET
    mock_get_response = MagicMock()
    mock_get_response.data = [
        {
            "id": "c1c1c1",
            "quantity": 1,
            "menu_items": {
                "id": cart_payload["menu_item_id"],
                "name": "Pizza",
                "price": 10.99,
                "image_url": "https://example.com/pizza.jpg",
                "restaurant_id": "r1",
            },
        }
    ]

    mock_get_chain = MagicMock()
    mock_get_chain.select.return_value.eq.return_value.execute.return_value = (
        mock_get_response
    )

    # Use side_effect to return different mocks for different calls
    mocker.patch(
        "cartRoutes.supabase.table",
        side_effect=[mock_post_chain, mock_get_chain],
    )

    # Add to cart
    post_response = client.post("/api/cart", json=cart_payload)
    assert post_response.status_code == 201

    # Get cart
    get_response = client.get(f"/api/cart?user_id={cart_payload['user_id']}")
    assert get_response.status_code == 200
    assert len(get_response.json) == 1


def test_add_then_remove_cart_flow(client, mocker, cart_payload):
    """
    Test adding an item then removing it (integration-style)
    """
    import cartRoutes

    # Mock for POST
    mock_post_response = MagicMock()
    mock_post_response.data = [{"id": "c1c1c1"}]

    mock_post_chain = MagicMock()
    mock_post_chain.upsert.return_value.execute.return_value = mock_post_response

    # Mock for DELETE
    mock_delete_response = MagicMock()
    mock_delete_response.data = [{"id": "c1c1c1"}]

    mock_delete_chain = MagicMock()
    mock_delete_chain.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
        mock_delete_response
    )

    mocker.patch(
        "cartRoutes.supabase.table",
        side_effect=[mock_post_chain, mock_delete_chain],
    )

    # Add to cart
    post_response = client.post("/api/cart", json=cart_payload)
    assert post_response.status_code == 201

    # Remove from cart
    delete_url = f"/api/cart/items/{cart_payload['menu_item_id']}?user_id={cart_payload['user_id']}"
    delete_response = client.delete(delete_url)
    assert delete_response.status_code == 204


def test_update_quantity_via_post(client, mocker, cart_payload):
    """
    Test updating quantity of existing cart item via POST (upsert behavior)
    """
    import cartRoutes

    # First add with quantity 1
    payload_v1 = cart_payload.copy()
    payload_v1["quantity"] = 1

    # Then update to quantity 3
    payload_v2 = cart_payload.copy()
    payload_v2["quantity"] = 3

    mock_response_v2 = MagicMock()
    mock_response_v2.data = [
        {
            "id": "c1c1c1",
            "user_id": payload_v2["user_id"],
            "menu_item_id": payload_v2["menu_item_id"],
            "quantity": 3,
        }
    ]

    mock_upsert_chain = MagicMock()
    mock_upsert_chain.upsert.return_value.execute.return_value = mock_response_v2

    mocker.patch("cartRoutes.supabase.table", return_value=mock_upsert_chain)

    response = client.post("/api/cart", json=payload_v2)

    assert response.status_code == 201
    assert response.json["quantity"] == 3
