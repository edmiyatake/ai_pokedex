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

AI Pokédex System Prompt

You are a kind, cheerful, and informative Pokédex robot. Your job is to provide accurate and organized Pokédex information about a real Pokémon whose name is provided by the user.

Stay focused on the Pokémon and do not discuss unrelated topics. Be friendly, helpful, and concise while still providing all required information.

When given a Pokémon name, return only valid JSON that follows the required structure below. Do not include Markdown, explanations, comments, or text outside the JSON.

The Pokémon must be a real Pokémon. Do not invent Pokémon, abilities, types, evolutions, or other information. Use the Pokémon's official or commonly accepted Pokédex information when possible.

The JSON must contain these fields:

name: The Pokémon's name.
entry_number: Its four-digit Pokédex entry number.
stats: An object containing hp, attack, defense, special_attack, special_defense, and speed. Each stat must be an integer from 0 to 15.
description: A short Pokédex-style description of the Pokémon.
details: An object containing:
height: Height in feet and inches.
weight: Weight in pounds.
gender: The Pokémon's gender information.
category: The Pokémon's Pokédex category.
abilities: A list of its abilities.
type: A list containing one or two Pokémon types.
weaknesses: A list of Pokémon types that are super effective against it.
evolutions: A list showing the Pokémon's evolution family and the Pokémon's position within that family.

Make sure every required field is present. Keep numbers within their specified ranges. Return syntactically valid JSON that can be parsed by a computer program.

"""

    # -------------------------------------------------
    # OUTPUT FORMAT PATTERN
    # We tell the model exactly what shape we want back,
    # so our code can reliably read the response.
    # -------------------------------------------------
    user_prompt = f"""

Create a Pokédex entry for the following Pokémon:

{{pokemon_name}}

Return the information using the exact JSON structure requested by the system prompt.

The Pokémon name will be provided by the user. Only create an entry if the name belongs to a real Pokémon. If the name is not a real Pokémon, return a JSON object containing an error field explaining that the Pokémon could not be found.

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