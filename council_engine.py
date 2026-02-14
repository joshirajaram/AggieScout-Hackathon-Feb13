import json
import os
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore", message=".*Python version 3.9.*")
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.auth")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.oauth2")

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

COUNCIL_MODEL = os.environ.get("COUNCIL_MODEL", "gemini-2.0-flash")
SCRIPT_DIR = Path(__file__).resolve().parent
SORCERER_JSON_PATH = SCRIPT_DIR / "sorcerer_mock_data.json"

AGRONOMIST_SYSTEM = (
    "You are a UC Davis Plant Pathologist. Analyze the image and the user's text to identify "
    "the agricultural issue. Be highly analytical and limit your response to two sentences."
)

WEATHER_SYSTEM = (
    "You are the Sorcerer Weather Node. Read the provided JSON data. State the immediate "
    "climate threat facing the farm right now in one concise sentence."
)

FOREMAN_SYSTEM = (
    "You are the Farm Foreman. You must make a final operational decision. Read the Agronomist's "
    "biological assessment and the Weather Node's climate data. Decide if the farmer should "
    "proceed with their requested action or delay it due to weather/costs. Limit your response to two sentences."
)


def _load_weather_json() -> str:
    try:
        with open(SORCERER_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return "{}"


def run_council(user_text: str, image_bytes: Optional[bytes] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    client = genai.Client(api_key=api_key)

    agronomist_parts: list[types.Part] = [types.Part.from_text(text=user_text)]
    if image_bytes:
        agronomist_parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        )
    agronomist_response = client.models.generate_content(
        model=COUNCIL_MODEL,
        contents=agronomist_parts,
        config=types.GenerateContentConfig(system_instruction=AGRONOMIST_SYSTEM),
    )
    agronomist_report = (agronomist_response.text or "").strip()

    weather_json_str = _load_weather_json()
    if weather_json_str == "{}":
        weather_report = "Weather data unavailable."
    else:
        weather_response = client.models.generate_content(
            model=COUNCIL_MODEL,
            contents=weather_json_str,
            config=types.GenerateContentConfig(system_instruction=WEATHER_SYSTEM),
        )
        weather_report = (weather_response.text or "").strip()

    combined = (
        f"User request: {user_text}\n\n"
        f"Agronomist assessment: {agronomist_report}\n\n"
        f"Weather report: {weather_report}"
    )
    foreman_response = client.models.generate_content(
        model=COUNCIL_MODEL,
        contents=combined,
        config=types.GenerateContentConfig(system_instruction=FOREMAN_SYSTEM),
    )
    foreman_decision = (foreman_response.text or "").strip()

    return (
        f"[Agronomist]: {agronomist_report}\n\n"
        f"[Weather Node]: {weather_report}\n\n"
        f"[Foreman]: {foreman_decision}"
    )


if __name__ == "__main__":
    dummy_text = "Should I spray the almonds today?"
    dummy_image: Optional[bytes] = None
    result = run_council(dummy_text, dummy_image)
    print(result)
