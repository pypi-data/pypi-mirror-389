from flask import Blueprint, jsonify, request, make_response
from extensions import supabase

# 1. Create a new, specific blueprint for the cart
cart_bp = Blueprint("cart", __name__)

# ----------------------------------------------------
# --- SHOPPING CART API ENDPOINTS ---
# ----------------------------------------------------


@cart_bp.route("/cart", methods=["POST"])
def add_to_cart():
    """
    Adds an item to the cart or updates its quantity if it already exists.
    This is an "upsert" operation.

    Expects JSON body:
    { "user_id": "...", "menu_item_id": "...", "quantity": 1 }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        menu_item_id = data.get("menu_item_id")
        quantity = data.get("quantity", 1)

        if not user_id or not menu_item_id:
            return make_response(
                jsonify({"error": "user_id and menu_item_id are required"}), 400
            )

        if int(quantity) < 1:
            # Logic to remove item if quantity drops to 0 or less
            # We call the other function directly
            return remove_from_cart(menu_item_id, user_id)

        response = (
            supabase.table("cart_items")
            .upsert(
                {
                    "user_id": user_id,
                    "menu_item_id": menu_item_id,
                    "quantity": quantity,
                },
                on_conflict="user_id, menu_item_id",
            )
            .execute()
        )

        if response.data:
            return jsonify(response.data[0]), 201

        return make_response(jsonify({"error": "Failed to update cart"}), 500)

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@cart_bp.route("/cart", methods=["GET"])
def get_cart():
    """
    Gets all items in a user's cart.
    Expects a query parameter: /api/cart?user_id=...
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return make_response(
                jsonify({"error": "user_id query parameter is required"}), 400
            )

        response = (
            supabase.table("cart_items")
            .select(
                """
                                id,
                                quantity,
                                menu_items (
                                    id,
                                    name,
                                    price,
                                    image_url,
                                    restaurant_id
                                )
                           """
            )
            .eq("user_id", user_id)
            .execute()
        )

        return jsonify(response.data)

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@cart_bp.route("/cart/items/<uuid:menu_item_id>", methods=["DELETE"])
def remove_from_cart(menu_item_id, user_id=None):
    """
    Removes a single item from a user's cart.
    Expects a query parameter: /api/cart/items/..._id_...?user_id=...
    """
    try:
        if not user_id:
            user_id = request.args.get("user_id")

        if not user_id:
            return make_response(
                jsonify({"error": "user_id query parameter is required"}), 400
            )

        response = (
            supabase.table("cart_items")
            .delete()
            .eq("user_id", user_id)
            .eq("menu_item_id", str(menu_item_id))
            .execute()
        )

        if not response.data:
            return make_response(jsonify({"error": "Item not found in cart"}), 404)

        return "", 204

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
