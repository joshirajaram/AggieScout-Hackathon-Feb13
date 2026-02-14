import json
import os
import sys
import warnings

warnings.filterwarnings("ignore", message=".*Python version 3.9.*")
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.auth")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.oauth2")

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

load_dotenv()

TEAMMATE_B_SYSTEM_PROMPT = (
    "You are an agricultural advisory assistant. You must output ONLY your recommended "
    "mitigation steps as plain text (bullets or short paragraphs). Never repeat, quote, or "
    "echo the sensor data or the user's question in your response."
)


def _fallback_mitigation(sensor_data: dict) -> str:
    temp = sensor_data.get("temp_f", 0)
    location = sensor_data.get("location") or sensor_data.get("crop") or "the field"
    if temp <= 32:
        return (
            "CRITICAL FROST – recommended steps:\n"
            "• Cover or move sensitive crops/equipment if possible.\n"
            "• Avoid irrigation; wet surfaces freeze faster.\n"
            "• Use wind machines or approved heating if available.\n"
            "• Check pipes and valves for freeze risk.\n"
            f"• Monitor {location} and repeat readings as conditions change."
        )
    return (
        "Conditions are above freezing. Recommended:\n"
        "• Continue normal monitoring.\n"
        "• Plan for possible frost if temps are expected to drop overnight.\n"
        f"• Keep an eye on {location} and humidity for disease risk."
    )


def get_mitigation_response(prompt: str, sensor_data=None) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and genai is not None:
        try:
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            if os.environ.get("DEBUG_LLM"):
                print("Gemini:", e, file=sys.stderr)

    if sensor_data is not None:
        return _fallback_mitigation(sensor_data)
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


def generate_alert(user_text: str, sensor_source: str = "frost") -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sensor_data = _read_sensor(script_dir, sensor_source)
    prefix, fallback_ref = _sensor_to_summary(sensor_data)

    system_prompt = _load_system_prompt()
    json_str = json.dumps(sensor_data, indent=2)
    final_text = f"{prefix}{json_str}\n\n{system_prompt}\n\n{user_text}"

    return get_mitigation_response(final_text, sensor_data=fallback_ref)


async def generate_alert_async(user_text: str, sensor_source: str = "frost") -> str:
    return generate_alert(user_text, sensor_source=sensor_source)


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "frost"
    if source not in ("frost", "heat", "normal"):
        print("Usage: python llm_engine.py [frost|heat|normal]")
        sys.exit(1)
    result = generate_alert("What should we do right now?", sensor_source=source)
    print(result)
