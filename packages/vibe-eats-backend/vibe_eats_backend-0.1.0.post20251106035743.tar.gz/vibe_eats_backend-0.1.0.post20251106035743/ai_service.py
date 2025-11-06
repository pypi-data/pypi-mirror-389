import json
from extensions import openai_client


def get_ai_recommendations(mood_text, restaurants_data):
    """
    Handles all AI-related logic for generating recommendations.
    """

    # 1. Format the restaurant data for the AI
    restaurant_prompt_data = _format_restaurants_for_ai(restaurants_data)

    # 2. Create the prompt
    prompt = f"""You are a food recommendation AI for "Vibe Eats". Based on the user's mood/feeling, recommend personalized restaurant dishes.

User's mood: "{mood_text}"

Available restaurants and dishes:
{restaurant_prompt_data}

Task: Analyze the user's mood and select 8-10 dishes from the list above that would best match their current feeling. Consider:
- Comfort foods for sad/stressed moods
- Light/healthy options for energetic/motivated moods
- Adventurous/exotic foods for excited/curious moods
- Familiar favorites for nostalgic moods

Return ONLY a JSON array of dish recommendations. For each dish, use the actual dish name from above and create a personalized description explaining why it matches the mood.

For each dish, use the image_url from the database. If the image_url starts with "/dishes/", prepend "https://xoworgfijegojldelcjv.supabase.co/storage/v1/object/public" to make it a full URL.
If no image_url exists, use "/placeholder.jpg".

[
  {{
    "id": <a unique number for each dish>,
    "menu_item_id": "<use the menu_item_id UUID from the list>",
    "restaurant_id": "<use the restaurant_id from the menu item>",
    "restaurant_name": "<use the restaurant name from the list>",
    "title": "<actual dish name from the list>",
    "description": "<why this specific dish matches their mood in 1-2 sentences>",
    "image": "<full image URL from database or /placeholder.jpg>",
    "price": <actual price from list>,
    "distance": <number between 1-5>,
    "rating": <number between 4.0-5.0>,
    "category": "<actual category from list>"
  }}
]

Important: Return ONLY the JSON array, no other text."""

    # 3. Call OpenAI API
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful food recommendation assistant that returns only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    # 4. Parse and return the response
    ai_response = completion.choices[0].message.content.strip()

    # Remove markdown code blocks if present
    if ai_response.startswith("```json"):
        ai_response = ai_response[7:]
    if ai_response.startswith("```"):
        ai_response = ai_response[3:]
    if ai_response.endswith("```"):
        ai_response = ai_response[:-3]
    ai_response = ai_response.strip()

    recommendations = json.loads(ai_response)
    return recommendations


# --- Helper Function (moved from your app.py) ---


def _format_restaurants_for_ai(restaurants):
    """Format restaurant data for the AI prompt."""
    formatted = []
    for restaurant in restaurants:
        restaurant_id = restaurant.get("id", "")
        restaurant_name = restaurant.get("name", "Unknown")
        restaurant_info = f"Restaurant: {restaurant_name} [restaurant_id: {restaurant_id}] - {restaurant.get('address', '')}"
        if "menu_items" in restaurant and restaurant["menu_items"]:
            dishes = []
            for item in restaurant["menu_items"]:
                item_id = item.get("id", "")
                name = item.get("name", "Unknown")
                description = item.get("description", "")
                category = item.get("category", "")
                price = item.get("price", 0)
                image_url = item.get("image_url", "/placeholder.jpg")
                dish = f"- {name} ({category}): {description} (${price}) [menu_item_id: {item_id}] [image_url: {image_url}]"
                dishes.append(dish)
            restaurant_info += "\n" + "\n".join(dishes)
        formatted.append(restaurant_info)
    return "\n\n".join(formatted)
