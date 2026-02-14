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

async def check_for_alerts():
    """Autonomous check for emergency conditions without user input."""
    # 1. Load System Prompt
    try:
        with open('prompts/system_prompt.txt', 'r') as f:
            system_instructions = f.read()
    except FileNotFoundError:
        try: 
            with open('system_prompt.txt', 'r') as f:
                system_instructions = f.read()
        except:
             system_instructions = "Act as an expert agricultural assistant."

    # 2. Load Sensor Data - simulating reading from the 'live' sensor in data/
    # For the hackathon, we'll pick one file or expect 'data/current.json'
    # Let's try to find a valid sensor file in data/
    sensor_data = {}
    try:
        # Check for a 'current.json' first, fallback to 'heat_sensor.json' for demo
        target_file = 'data/heat_sensor.json' 
        if os.path.exists('data/current_sensor.json'):
            target_file = 'data/current_sensor.json'
            
        with open(target_file, 'r') as f:
            sensor_data = json.load(f)
    except Exception as e:
        return None # No data, no alert

    # 3. Failsafe Logic + Weather
    temp = sensor_data.get('temp_f', 70)
    weather_data = get_weather_data()
    
    # Simple Heuristic Trigger for the Hackathon
    # Use LLM to decide if it's worthy of an alert
    if temp >= 90 or temp <= 35:
        prompt = (
            f"{system_instructions}\n\n"
            f"TASK: Analyze this situation and generate a short EMERGENCY ALERT if needed. If no emergency, return 'NO_ALERT'.\n"
            f"REAL-TIME WEATHER: {json.dumps(weather_data)}\n"
            f"FIELD SENSORS: {json.dumps(sensor_data)}\n"
        )
        response = get_gemini_response(prompt)
        if "NO_ALERT" not in response:
            return response
            
    return None

async def generate_response(user_text):
    """Responds to user queries."""
    
    # 1. Load System Prompt
    try:
        with open('prompts/system_prompt.txt', 'r') as f:
            system_instructions = f.read()
    except:
        system_instructions = "Act as an expert agricultural assistant."

    # 2. Load Sensor Data
    try:
        target_file = 'data/heat_sensor.json'
        if os.path.exists('data/current_sensor.json'):
            target_file = 'data/current_sensor.json'
        with open(target_file, 'r') as f:
            sensor_data = json.load(f)
    except Exception as e:
        sensor_data = {"error": "No sensor data"}

    weather_data = get_weather_data()
    
    final_prompt = (
        f"{system_instructions}\n\n"
        f"CURRENT WEATHER (Davis, CA): {json.dumps(weather_data)}\n"
        f"FIELD SENSORS: {json.dumps(sensor_data)}\n"
        f"USER QUESTION: {user_text}\n"
    )

    return get_gemini_response(final_prompt)