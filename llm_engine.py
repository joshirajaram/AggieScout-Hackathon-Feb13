import json
import os
import sys
import warnings
from typing import Optional

warnings.filterwarnings("ignore", message=".*Python version 3.9.*")
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.auth")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.oauth2")

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

load_dotenv()

TEAMMATE_B_SYSTEM_PROMPT = (
    "You are an agricultural advisory assistant. You MUST answer the specific question "
    "the farmer asked. Do not give a generic summary—respond directly to what they asked "
    "using the sensor data provided. Use plain text, bullets or short paragraphs. "
    "Never repeat or echo the raw sensor JSON in your response."
)


def _fallback_mitigation(user_query: str, sensor_data: dict) -> str:
    temp = sensor_data.get("temp_f", 0)
    humidity = sensor_data.get("humidity", 0)
    wind = sensor_data.get("wind_mph", 0)
    location = sensor_data.get("location") or sensor_data.get("crop") or "the field"
    
    query = user_query.lower()
    
    # Enhanced keyword-based logic for fallback
    if query.strip() in ("hi", "hello", "hey", "start", "/start", "help"):
        if temp <= 32:
            return f"Hello. WARNING: Current temp is {temp}°F (Critical Frost). Please check your crops immediately."
        return f"Hello! Current conditions: {temp}°F, Wind {wind} mph, Humidity {humidity}%."
         
    if "irrigat" in query or "water" in query:  # Matches "irrigate", "irrigation"
        if temp > 90:
            return f"High temp ({temp}°F) detected. Increase irrigation frequency for {location} immediately to prevent heat stress."
        elif temp < 35:
            return f"Low temp ({temp}°F) detected. Avoid irrigation to prevent freezing on plants unless using for frost protection."
        elif humidity > 80:
            return f"Humidity is high ({humidity}%). Reduce irrigation to prevent fungal issues."
        return f"Soil moisture logic unavailable, but environmental conditions (Temp: {temp}°F) are stable. maintain standard irrigation schedule for {location}."
        
    if "spray" in query or "pesticide" in query or "fertilizer" in query or "treat" in query:
        if wind > 10:
            return f"Wind is {wind} mph. Do NOT spray; drift risk is high."
        if temp > 85:
            return f"Temp is {temp}°F. Avoid spraying; evaporation/burn risk is high."
        if temp < 40:
            return f"Temp is low ({temp}°F). Spraying may be ineffective or cause freezing damage."
        return f"Conditions (Wind: {wind} mph, Temp: {temp}°F) are suitable for spraying."
        
    if "harvest" in query:
        if humidity > 80:
            return f"High humidity ({humidity}%) may affect harvest quality/drying."
        if temp > 95:
            return f"Extreme heat ({temp}°F). Ensure worker safety during harvest."
        return f"Conditions seem favorable for harvest operations."

    # Any other question: acknowledge it and respond using current conditions (no keyword match)
    cond = f"Current conditions: {temp}°F, wind {wind} mph, humidity {humidity}% at {location}."
    if temp <= 32:
        return (
            f"You asked: \"{user_query}\"\n\n"
            f"{cond} CRITICAL FROST risk.\n\n"
            "• Cover or move sensitive crops if possible; avoid irrigation; use wind machines or heating if available; check pipes for freeze risk."
        )
    if temp >= 95:
        return (
            f"You asked: \"{user_query}\"\n\n"
            f"{cond} High heat.\n\n"
            "• Increase irrigation frequency, provide shade/ventilation where possible, and monitor for heat stress."
        )
    return (
        f"You asked: \"{user_query}\"\n\n"
        f"{cond}\n\n"
        "• Conditions are in a moderate range. Continue normal monitoring; use the crop rules in the app for frost/heat thresholds."
    )


def get_mitigation_response(
    user_query: str,
    sensor_context: str,
    system_prompt: str,
    sensor_data=None,
) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and genai is not None and types is not None:
        try:
            client = genai.Client(api_key=gemini_key)
            user_message = (
                f"The farmer asks: \"{user_query}\"\n\n"
                f"Answer this specific question using only the sensor data below. Do not ignore the question.\n\n"
                f"Sensor data:\n{sensor_context}"
            )
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=user_message,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            if os.environ.get("DEBUG_LLM"):
                print("Gemini:", e, file=sys.stderr)

    if sensor_data is not None:
        return _fallback_mitigation(user_query, sensor_data)
    return (
        "Mitigation: Check sensor and protect plants. Cover sensitive crops; "
        "avoid irrigation. [Set GEMINI_API_KEY in .env.]"
    )


def _load_system_prompt() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "prompts", "system_prompt.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return TEAMMATE_B_SYSTEM_PROMPT


def _read_sensor(script_dir: str, source: str):
    path = os.path.join(script_dir, "data", f"{source}_sensor.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _sensor_to_summary(sensor_data: list) -> tuple[str, object]:
    if not sensor_data:
        return "", None
    readings = sensor_data
    min_temp = min(r.get("temp_f", 0) for r in readings)
    max_temp = max(r.get("temp_f", 0) for r in readings)
    if min_temp <= 28:
        prefix = "CRITICAL FROST DETECTED. "
    elif max_temp >= 100:
        prefix = "CRITICAL HEAT. "
    else:
        prefix = ""
    return prefix, readings[0]


def _infer_sensor_source(user_text: str) -> str:
    """Pick frost/heat/normal from the user's question when obvious."""
    q = user_text.lower().strip()
    if not q:
        return "frost"
    if any(w in q for w in ("heat", "hot", "summer", "drought", "102", "100")):
        return "heat"
    if any(w in q for w in ("normal", "ok", "baseline", "routine")):
        return "normal"
    return "frost"


def generate_alert(user_text: str, sensor_source: Optional[str] = None) -> str:
    if sensor_source is None:
        sensor_source = _infer_sensor_source(user_text)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sensor_data = _read_sensor(script_dir, sensor_source)
    prefix, fallback_ref = _sensor_to_summary(sensor_data)

    system_prompt = _load_system_prompt()
    json_str = json.dumps(sensor_data, indent=2)
    sensor_context = f"{prefix}{json_str}" if prefix else json_str

    return get_mitigation_response(
        user_query=user_text,
        sensor_context=sensor_context,
        system_prompt=system_prompt,
        sensor_data=fallback_ref,
    )


async def generate_alert_async(user_text: str, sensor_source: Optional[str] = None) -> str:
    return generate_alert(user_text, sensor_source=sensor_source)


if __name__ == "__main__":
    argv = sys.argv[1:]
    source = argv[0] if argv and argv[0] in ("frost", "heat", "normal") else "frost"
    query = " ".join(argv[1:]).strip() if len(argv) > 1 else "What should we do right now?"
    if not query:
        query = "What should we do right now?"
    if argv and argv[0] not in ("frost", "heat", "normal"):
        print("Usage: python llm_engine.py [frost|heat|normal] [your question]")
        sys.exit(1)
    result = generate_alert(query, sensor_source=source)
    print(result)
