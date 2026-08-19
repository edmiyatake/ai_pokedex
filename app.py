"""
AI Pokedex - Backend
Teaching topics: prompt patterns, the ChatGPT API, prompt roles, JSON responses

Run with: python app.py
Then open http://localhost:5000 in your browser
"""

from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ---------------------------------------------------------
# Serve the frontend
# ---------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# ---------------------------------------------------------
# The main Pokedex endpoint
# ---------------------------------------------------------
@app.route("/api/pokedex", methods=["POST"])
def pokedex():
    data = request.get_json()
    pokemon_name = data.get("name", "")
    persona = data.get("persona", "a helpful, knowledgeable Pokedex")

    if not pokemon_name:
        return jsonify({"error": "Please provide a Pokemon name"}), 400

    # -------------------------------------------------
    # PERSONA PATTERN
    # The system prompt gives the model an identity and
    # behavior rules for how it writes descriptions.
    # -------------------------------------------------
    system_prompt = f"""
You are a Pokedex with the personality of {persona}.
You generate detailed Pokedex entries in that voice.
The Pokemon can be real or made up.
Stay in character in the description field only. Every other field
must contain plain factual data, not personality.
"""

    # -------------------------------------------------
    # OUTPUT FORMAT PATTERN
    # We tell the model exactly what shape we want back,
    # so our code can reliably read the response.
    # -------------------------------------------------
    user_prompt = f"""
Generate a Pokedex entry for "{pokemon_name}".
Respond with ONLY valid JSON, no extra text, in this exact shape:

{{
  "name": "string",
  "entry_number": "4 digit string, like 025",
  "stats": {{
    "hp": "integer 0-15",
    "attack": "integer 0-15",
    "defense": "integer 0-15",
    "special_attack": "integer 0-15",
    "special_defense": "integer 0-15",
    "speed": "integer 0-15"
  }},
  "description": "1-2 sentences in your persona's voice",
  "details": {{
    "height": "string, feet and inches, like 1'04\\"",
    "weight": "string, pounds, like 13.2 lbs",
    "gender": "male, female, or male/female",
    "category": "string, like Mouse Pokemon",
    "abilities": ["list", "of", "strings"]
  }},
  "types": ["list of 1 or 2 strings"],
  "weaknesses": ["list of strings"],
  "evolutions": ["ordered list of strings, like Pichu #172, Pikachu #025, Raichu #026"]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_text = response.choices[0].message.content

    # -------------------------------------------------
    # Models don't always follow instructions perfectly.
    # Always handle the case where JSON parsing fails.
    # -------------------------------------------------
    try:
        pokemon_data = json.loads(raw_text)
    except json.JSONDecodeError:
        return jsonify({
            "error": "The AI didn't return valid JSON. Try again.",
            "raw_response": raw_text,
        }), 500

    return jsonify(pokemon_data)


if __name__ == "__main__":
    app.run(debug=True)