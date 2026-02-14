import json
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_weather_data():
    """Fetches current weather data for Davis, CA using Open-Meteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 38.5449,
            "longitude": -121.7405,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('current', {})
        else:
            return {"error": f"Failed to fetch weather: {response.status_code}"}
    except Exception as e:
        return {"error": f"Exception fetching weather: {str(e)}"}

def get_gemini_response(prompt):
    """Sends the prompt to the Gemini LLM."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: Gemini API returned invalid response - {str(e)}"

async def generate_alert(user_text):
    """The main bridge between sensor data, user input, and the LLM."""
    
    # 1. Load the System Prompt (Teammate 2's instructions)
    try:
        with open('system_prompt.txt', 'r') as f:
            system_instructions = f.read()
    except FileNotFoundError:
        system_instructions = "Act as an expert agricultural assistant."

    # 2. Load the Sensor Data (Teammate 2's JSON files)
    try:
        # Assuming Teammate 2 renames the active file to current_sensor.json for the demo
        with open('current_sensor.json', 'r') as f:
            sensor_data = json.load(f)
    except Exception as e:
        return f"Error reading sensors: {str(e)}"

    # 3. Failsafe Logic: Add emergency context before the LLM even sees it
    temp = sensor_data.get('temp_f', 70)
    emergency_prefix = ""
    if temp <= 32:
        emergency_prefix = "⚠️ CRITICAL FROST DETECTED! IMMEDIATE ACTION REQUIRED.\n"
    elif temp >= 95:
        emergency_prefix = "🔥 EXTREME HEAT ALERT! IRRIGATION STRESS LIKELY.\n"

    # 4. Combine everything into one contextual prompt
    weather_data = get_weather_data()
    final_prompt = (
        f"{system_instructions}\n\n"
        f"CURRENT REAL-TIME WEATHER FOR DAVIS, CA: {json.dumps(weather_data)}\n"
        f"CURRENT FIELD DATA (JSON): {json.dumps(sensor_data)}\n\n"
        f"USER QUESTION: {user_text}\n\n"
        f"CONTEXT: {emergency_prefix}\n"
        "Please analyze the user's question in the context of the current weather and field data."
    )

    # 5. Get the AI to reason through the data
    # Note: Using a synchronous call in an async function can block the bot.
    # For a hackathon demo, this is fine. For production, use 'httpx' or 'aiohttp'.
    result = get_gemini_response(final_prompt)
    
    return f"{emergency_prefix}{result}"