"""
Gemini AI Service for PocketSmart AI
Handles prompt construction and calls to Gemini 1.5 Flash
"""

import os
import json
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"


def get_model():
    return genai.GenerativeModel(MODEL_NAME)


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Extract JSON from Gemini response that may contain markdown fences."""
    text = text.strip()
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to find first { ... }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "error": "Failed to parse AI response",
            "raw": text[:500],
            "allocations": [],
            "summary": "Could not generate structured recommendations. Please try again.",
            "tips": ["Ensure your API key is valid", "Try with a clearer budget description"],
        }


def generate_home_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate home interior recommendations based on budget and items."""
    rooms = ", ".join([r if isinstance(r, str) else r.value for r in data.get("rooms", [])])
    items_desc = []
    for item in data.get("items", []):
        cat = item.get("category", "item")
        qty = item.get("quantity", 1)
        style = item.get("preferred_style", "modern")
        items_desc.append(f"{qty}x {cat} ({style})")
    items_str = "; ".join(items_desc) if items_desc else "general furniture and decor"
    platforms = ", ".join(data.get("preferred_platforms", ["Amazon", "Flipkart", "IKEA"]))
    style = data.get("style", "modern")
    notes = data.get("additional_notes") or "None"

    prompt = f"""You are PocketSmart AI, an expert home interior budget planner for the Indian market (prices in INR).

User Request:
- Total Budget: ₹{data.get('budget', 0):,.0f}
- Rooms: {rooms}
- Items needed: {items_str}
- Preferred style: {style}
- Preferred platforms: {platforms}
- Additional notes: {notes}

Task:
1. Allocate the total budget intelligently across the requested categories/items.
2. For each category suggest 2-3 realistic product recommendations available on {platforms}.
3. Keep total of estimated prices within or very close to the budget.
4. Include approximate product URLs (search-style) for Amazon, Flipkart or IKEA India.

Respond ONLY with valid JSON in this exact structure (no extra text):
{{
  "planner_type": "home",
  "total_budget": {data.get('budget', 0)},
  "remaining_budget": <number>,
  "allocations": [
    {{
      "category": "<category name>",
      "allocated_budget": <number>,
      "percentage": <number 0-100>,
      "recommendations": [
        {{
          "name": "<product name>",
          "category": "<same category>",
          "estimated_price": <number>,
          "platform": "<Amazon|Flipkart|IKEA>",
          "description": "<short description>",
          "why_recommended": "<why it fits budget & style>",
          "product_url": "<https://... search or product link>"
        }}
      ]
    }}
  ],
  "summary": "<2-3 sentence overall summary>",
  "tips": ["<tip1>", "<tip2>", "<tip3>"]
}}
"""

    try:
        model = get_model()
        response = model.generate_content(prompt)
        result = _safe_parse_json(response.text)
        result["generated_at"] = datetime.utcnow().isoformat() + "Z"
        return result
    except Exception as e:
        return _fallback_home(data, str(e))


def generate_party_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate party planning recommendations."""
    event = data.get("event_type", "birthday")
    if hasattr(event, "value"):
        event = event.value
    platforms = ", ".join(data.get("preferred_platforms", ["Swiggy", "Zomato", "OYO", "Amazon"]))
    notes = data.get("additional_notes") or "None"
    venue = data.get("venue_preference") or "flexible"
    city = data.get("city") or "Mumbai"

    prompt = f"""You are PocketSmart AI, an expert party/event budget planner for the Indian market (prices in INR).

User Request:
- Total Budget: ₹{data.get('budget', 0):,.0f}
- Guest Count: {data.get('guest_count', 10)}
- Event Type: {event}
- Venue Preference: {venue}
- City: {city}
- Preferred platforms: {platforms}
- Additional notes: {notes}

Task:
1. Allocate budget proportionally across: Catering/Food, Decoration, Venue/Accommodation (if needed), Entertainment, Miscellaneous.
2. Suggest realistic options from Swiggy, Zomato (food), OYO (venues), Amazon/Flipkart (decor & supplies).
3. Keep recommendations practical for {event} with {data.get('guest_count')} guests.
4. Total estimated spend should stay within budget.

Respond ONLY with valid JSON:
{{
  "planner_type": "party",
  "total_budget": {data.get('budget', 0)},
  "remaining_budget": <number>,
  "allocations": [
    {{
      "category": "<Catering|Decoration|Venue|Entertainment|Misc>",
      "allocated_budget": <number>,
      "percentage": <number>,
      "recommendations": [
        {{
          "name": "<option name>",
          "category": "<same>",
          "estimated_price": <number>,
          "platform": "<Swiggy|Zomato|OYO|Amazon|Flipkart>",
          "description": "<short description>",
          "why_recommended": "<reason>",
          "product_url": "<https://...>"
        }}
      ]
    }}
  ],
  "summary": "<summary>",
  "tips": ["tip1", "tip2", "tip3"]
}}
"""

    try:
        model = get_model()
        response = model.generate_content(prompt)
        result = _safe_parse_json(response.text)
        result["generated_at"] = datetime.utcnow().isoformat() + "Z"
        return result
    except Exception as e:
        return _fallback_party(data, str(e))


def generate_jewelry_recommendations(
    data: Dict[str, Any], image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """Generate jewelry recommendations. Supports optional outfit image."""
    platforms = ", ".join(data.get("preferred_platforms", ["Amazon", "Flipkart"]))
    style = data.get("style", "contemporary")
    if hasattr(style, "value"):
        style = style.value
    metal = data.get("metal_preference") or "any"
    notes = data.get("additional_notes") or "None"
    occasion = data.get("occasion", "general")

    text_prompt = f"""You are PocketSmart AI, an expert jewelry recommendation assistant for the Indian market (prices in INR).

User Request:
- Total Budget: ₹{data.get('budget', 0):,.0f}
- Occasion: {occasion}
- Preferred style: {style}
- Metal preference: {metal}
- Preferred platforms: {platforms}
- Additional notes: {notes}
{"- An outfit image has been provided. Analyze colors, style and formality to suggest matching jewelry." if image_bytes else ""}

Task:
1. Suggest 3-5 jewelry pieces or sets that fit the budget, occasion and style.
2. If an image is provided, coordinate colors and formality with the outfit.
3. Prefer items commonly available on Amazon India and Flipkart.
4. Stay within the total budget.

Respond ONLY with valid JSON:
{{
  "planner_type": "jewelry",
  "total_budget": {data.get('budget', 0)},
  "remaining_budget": <number>,
  "allocations": [
    {{
      "category": "Jewelry",
      "allocated_budget": <number>,
      "percentage": 100,
      "recommendations": [
        {{
          "name": "<jewelry name>",
          "category": "Jewelry",
          "estimated_price": <number>,
          "platform": "<Amazon|Flipkart>",
          "description": "<description>",
          "why_recommended": "<why it matches occasion/outfit/budget>",
          "product_url": "<https://...>"
        }}
      ]
    }}
  ],
  "summary": "<summary including color/style match if image provided>",
  "tips": ["tip1", "tip2", "tip3"]
}}
"""

    try:
        model = get_model()
        if image_bytes:
            import PIL.Image
            import io
            img = PIL.Image.open(io.BytesIO(image_bytes))
            response = model.generate_content([text_prompt, img])
        else:
            response = model.generate_content(text_prompt)
        result = _safe_parse_json(response.text)
        result["generated_at"] = datetime.utcnow().isoformat() + "Z"
        return result
    except Exception as e:
        return _fallback_jewelry(data, str(e))


# ---------- Fallback mock responses (used when API key missing or error) ----------

def _fallback_home(data: Dict, error: str = "") -> Dict:
    budget = float(data.get("budget", 50000))
    return {
        "planner_type": "home",
        "total_budget": budget,
        "remaining_budget": budget * 0.05,
        "allocations": [
            {
                "category": "Lighting",
                "allocated_budget": budget * 0.2,
                "percentage": 20,
                "recommendations": [
                    {
                        "name": "LED Ceiling Light (Set of 2)",
                        "category": "Lighting",
                        "estimated_price": budget * 0.08,
                        "platform": "Amazon",
                        "description": "Energy-efficient warm white LED lights suitable for living areas.",
                        "why_recommended": "Affordable, high ratings, fits modern style.",
                        "product_url": "https://www.amazon.in/s?k=led+ceiling+light",
                    },
                    {
                        "name": "Modern Floor Lamp",
                        "category": "Lighting",
                        "estimated_price": budget * 0.07,
                        "platform": "IKEA",
                        "description": "Minimalist floor lamp with adjustable height.",
                        "why_recommended": "Complements contemporary interiors.",
                        "product_url": "https://www.ikea.com/in/en/search/?q=floor%20lamp",
                    },
                ],
            },
            {
                "category": "Furniture",
                "allocated_budget": budget * 0.55,
                "percentage": 55,
                "recommendations": [
                    {
                        "name": "Fabric Sofa (3-seater)",
                        "category": "Furniture",
                        "estimated_price": budget * 0.35,
                        "platform": "Flipkart",
                        "description": "Comfortable sofa with soft cushions, multiple colour options.",
                        "why_recommended": "Best value under budget for living room.",
                        "product_url": "https://www.flipkart.com/search?q=3+seater+sofa",
                    },
                    {
                        "name": "Coffee Table - Wooden",
                        "category": "Furniture",
                        "estimated_price": budget * 0.12,
                        "platform": "IKEA",
                        "description": "Solid wood coffee table with storage shelf.",
                        "why_recommended": "Durable and stylish.",
                        "product_url": "https://www.ikea.com/in/en/search/?q=coffee%20table",
                    },
                ],
            },
            {
                "category": "Decor",
                "allocated_budget": budget * 0.2,
                "percentage": 20,
                "recommendations": [
                    {
                        "name": "Wall Art Canvas Set",
                        "category": "Decor",
                        "estimated_price": budget * 0.08,
                        "platform": "Amazon",
                        "description": "Set of 3 abstract art prints.",
                        "why_recommended": "Adds personality without overspending.",
                        "product_url": "https://www.amazon.in/s?k=wall+art+canvas",
                    }
                ],
            },
        ],
        "summary": f"Mock recommendations generated for a ₹{budget:,.0f} home budget. "
                   f"{'(Gemini API unavailable: ' + error + ')' if error else 'Using demo data because GEMINI_API_KEY is not set.'}",
        "tips": [
            "Compare prices across Amazon, Flipkart and IKEA before buying.",
            "Check return policies and delivery timelines.",
            "Prioritise high-use items (sofa, lighting) within budget.",
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "is_fallback": True,
    }


def _fallback_party(data: Dict, error: str = "") -> Dict:
    budget = float(data.get("budget", 30000))
    guests = int(data.get("guest_count", 20))
    return {
        "planner_type": "party",
        "total_budget": budget,
        "remaining_budget": budget * 0.05,
        "allocations": [
            {
                "category": "Catering",
                "allocated_budget": budget * 0.45,
                "percentage": 45,
                "recommendations": [
                    {
                        "name": f"Veg/Non-Veg Party Pack for {guests}",
                        "category": "Catering",
                        "estimated_price": budget * 0.35,
                        "platform": "Swiggy",
                        "description": "Multi-cuisine party platter with starters and main course.",
                        "why_recommended": "Convenient bulk ordering with good reviews.",
                        "product_url": "https://www.swiggy.com",
                    },
                    {
                        "name": "Dessert & Beverages Combo",
                        "category": "Catering",
                        "estimated_price": budget * 0.08,
                        "platform": "Zomato",
                        "description": "Cake + soft drinks / mocktails package.",
                        "why_recommended": "Completes the menu within remaining catering budget.",
                        "product_url": "https://www.zomato.com",
                    },
                ],
            },
            {
                "category": "Decoration",
                "allocated_budget": budget * 0.25,
                "percentage": 25,
                "recommendations": [
                    {
                        "name": "Balloon & Banner Decoration Kit",
                        "category": "Decoration",
                        "estimated_price": budget * 0.12,
                        "platform": "Amazon",
                        "description": "Complete theme decoration set.",
                        "why_recommended": "Easy DIY, looks premium.",
                        "product_url": "https://www.amazon.in/s?k=party+decoration+kit",
                    }
                ],
            },
            {
                "category": "Venue / Stay",
                "allocated_budget": budget * 0.2,
                "percentage": 20,
                "recommendations": [
                    {
                        "name": "OYO Party Hall / Rooms (if needed)",
                        "category": "Venue",
                        "estimated_price": budget * 0.18,
                        "platform": "OYO",
                        "description": "Affordable banquet or multiple rooms for overnight guests.",
                        "why_recommended": "Budget-friendly venue option.",
                        "product_url": "https://www.oyorooms.com",
                    }
                ],
            },
        ],
        "summary": f"Demo party plan for {guests} guests within ₹{budget:,.0f}. "
                   f"{'(API error: ' + error + ')' if error else 'Set GEMINI_API_KEY for live AI recommendations.'}",
        "tips": [
            "Book catering 2-3 days in advance for better rates.",
            "Confirm guest count early to avoid food waste.",
            "Mix DIY decor with ready kits to save money.",
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "is_fallback": True,
    }


def _fallback_jewelry(data: Dict, error: str = "") -> Dict:
    budget = float(data.get("budget", 15000))
    occasion = data.get("occasion", "party")
    return {
        "planner_type": "jewelry",
        "total_budget": budget,
        "remaining_budget": budget * 0.1,
        "allocations": [
            {
                "category": "Jewelry",
                "allocated_budget": budget * 0.9,
                "percentage": 90,
                "recommendations": [
                    {
                        "name": "Elegant Necklace Set",
                        "category": "Jewelry",
                        "estimated_price": budget * 0.45,
                        "platform": "Amazon",
                        "description": f"Stylish necklace + earring set ideal for {occasion}.",
                        "why_recommended": "Popular choice under budget with good customer ratings.",
                        "product_url": "https://www.amazon.in/s?k=necklace+set",
                    },
                    {
                        "name": "Statement Earrings",
                        "category": "Jewelry",
                        "estimated_price": budget * 0.25,
                        "platform": "Flipkart",
                        "description": "Lightweight earrings that match most outfits.",
                        "why_recommended": "Versatile and budget-friendly.",
                        "product_url": "https://www.flipkart.com/search?q=statement+earrings",
                    },
                    {
                        "name": "Bracelet / Bangle",
                        "category": "Jewelry",
                        "estimated_price": budget * 0.15,
                        "platform": "Amazon",
                        "description": "Minimal or traditional bracelet depending on style.",
                        "why_recommended": "Completes the look without exceeding budget.",
                        "product_url": "https://www.amazon.in/s?k=bracelet",
                    },
                ],
            }
        ],
        "summary": f"Demo jewelry suggestions for {occasion} within ₹{budget:,.0f}. "
                   f"{'(API error: ' + error + ')' if error else 'Add GEMINI_API_KEY for personalized AI + image analysis.'}",
        "tips": [
            "Check metal purity and return policy before purchase.",
            "Match jewelry metal tone with outfit accessories.",
            "Consider artificial jewellery for higher quantity within budget.",
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "is_fallback": True,
    }
