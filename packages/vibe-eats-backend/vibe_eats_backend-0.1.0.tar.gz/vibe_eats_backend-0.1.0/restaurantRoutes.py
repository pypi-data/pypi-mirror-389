from flask import Blueprint, jsonify, request, make_response

# Import the supabase client from your main app.py
from extensions import supabase
import ai_service  # <-- Import your new service file
import json

# 1. Create a Blueprint object
# 'api' is the name of this blueprint.
api_blueprint = Blueprint("api", __name__)

# --- API ROUTES ---


# 2. Change @app.route to @api_blueprint.route
# 3. Note the URL is now just '/restaurants', not '/api/restaurants'.
#    We will add the '/api' prefix when we register the blueprint.
@api_blueprint.route("/restaurants", methods=["GET"])
def get_restaurants():
    """
    Retrieves all restaurants from the database.
    """
    try:
        response = supabase.table("restaurants").select("*").execute()

        if response.data:
            return jsonify(response.data)
        return jsonify({"error": "No restaurants found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Full URL will be: /api/restaurant/<uuid:restaurant_id>
@api_blueprint.route("/restaurant/<uuid:restaurant_id>", methods=["GET"])
def get_restaurant_details(restaurant_id):
    """
    Retrieves a single restaurant and its associated menu items.
    """
    try:
        response = (
            supabase.table("restaurants")
            .select("*, menu_items(*)")
            .eq("id", str(restaurant_id))
            .execute()
        )

        if response.data:
            # 3. Return the *first item* from the list
            return jsonify(response.data[0])

        # 4. If the list is empty, it's a 404
        return (jsonify({"error": "Restaurant not found"}), 404)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Full URL will be: /api/restaurants (on a POST)
@api_blueprint.route("/restaurants", methods=["POST"])
def create_restaurant():
    """
    Creates a new restaurant and its menu items.
    """
    new_restaurant_id = None

    try:
        data = request.get_json()

        print(data)

        if not data or not data.get("name"):
            return jsonify({"error": "Restaurant name is required"}), 400

        # --- Step 1: Create the Restaurant ---
        restaurant_data = {
            "name": data.get("name"),
            "address": data.get("address"),
            "banner_image_url": data.get("banner_image_url"),
        }

        restaurant_response = (
            supabase.table("restaurants").insert(restaurant_data).execute()
        )

        if not restaurant_response.data:
            raise Exception(
                "Failed to create restaurant. Response: "
                + str(restaurant_response.error or "No data returned")
            )

        new_restaurant = restaurant_response.data[0]
        new_restaurant_id = new_restaurant["id"]

        # --- Step 2: Create the Menu Items ---
        menu_items_data = data.get("menu_items", [])
        inserted_menu_items = []

        if menu_items_data:
            for item in menu_items_data:
                item["restaurant_id"] = new_restaurant_id

            menu_response = (
                supabase.table("menu_items").insert(menu_items_data).execute()
            )

            if not menu_response.data:
                supabase.table("restaurants").delete().eq(
                    "id", new_restaurant_id
                ).execute()
                raise Exception(
                    "Menu items failed to save. Restaurant creation was rolled back."
                )

            inserted_menu_items = menu_response.data

        # --- Step 3: Success! ---
        new_restaurant["menu_items"] = inserted_menu_items
        return jsonify(new_restaurant), 201

    except Exception as e:
        if new_restaurant_id:
            supabase.table("restaurants").delete().eq("id", new_restaurant_id).execute()

        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@api_blueprint.route("/recommendations", methods=["POST"])
def get_recommendations():
    try:
        data = request.get_json()
        mood_text = data.get("mood", "")

        if not mood_text:
            return make_response(jsonify({"error": "Mood text is required"}), 400)

        # 1. Get all restaurants from Supabase
        restaurants_response = (
            supabase.table("restaurants").select("*, menu_items(*)").execute()
        )

        if not restaurants_response.data:
            return make_response(
                jsonify({"error": "No restaurants available in database"}), 404
            )

        # 2. Call the AI service to do the heavy lifting
        recommendations = ai_service.get_ai_recommendations(
            mood_text, restaurants_response.data
        )

        return jsonify({"recommendations": recommendations})

    except json.JSONDecodeError as e:
        return make_response(
            jsonify({"error": "Failed to parse AI response", "details": str(e)}), 500
        )
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
