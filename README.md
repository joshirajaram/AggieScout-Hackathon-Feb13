# AggieScout - Agricultural Assistant Bot 🌿

AggieScout is an AI-powered Telegram bot designed to help farmers monitor their fields, analyze sensor data, and receive real-time alerts. It integrates local sensor data with real-time weather information for Davis, CA, and uses Google's Gemini LLM to provide intelligent, context-aware agricultural advice.

## Features

*   **Autonomous Agent**: Continuously monitors sensor data in the background and proactively alerts the farmer via Telegram if critical conditions are detected.
*   **Real-time Weather Integration**: Fetches current weather conditions (temperature, humidity, wind) for Davis, CA using the Open-Meteo API.
*   **Field Sensor Monitoring**: Analyzes JSON sensor data for critical conditions.
*   **Intelligent Alerts**:
    *   **Frost Warning**: Detects temperatures below freezing.
    *   **Heat Stress**: Detects dangerous heat levels.
*   **AI Reasoning**: Uses Google Gemini Pro to answer user queries and generate alerts in the context of currently available data.

## Prerequisites

*   Python 3.10 or higher (Confirmed working with 3.13)
*   A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
*   A Google Gemini API Key

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd AggieScout-Hackathon-Feb13
    ```

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Required packages: `python-telegram-bot`, `python-dotenv`, `google-generativeai`, `requests`.*

## Configuration

1.  **Environment Variables:**
    Create a `.env` file in the project root to store your API keys securely:
    ```bash
    touch .env
    ```
    Add your Gemini API Key to the `.env` file:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

2.  **Bot Token:**
    Update the `token` string in `bot.py` with your Telegram Bot Token.

3.  **Data Setup:**
    The bot expects sensor data in `data/current_sensor.json`. You can copy one of the sample files to simulate conditions:
    ```bash
    cp data/heat_sensor.json data/current_sensor.json
    ```

## Running the Bot

Start the bot by running:

```bash
python3 bot.py
```

1.  Open your bot in Telegram and click **Start**.
2.  The bot will reply confirming it is online.
3.  **Autonomous Alerts:** The bot will automatically check sensor data every 10 seconds. If `data/current_sensor.json` contains extreme values (like heat or frost), you will receive an alert without typing anything.
4.  **Chat:** You can also ask questions like "How is the soil moisture?" or "Should I irrigate?".

## Project Structure

*   `bot.py`: The entry point. Handles Telegram connection and schedules the autonomous background job.
*   `llm_engine.py`: The "Brain". Connects to Gemini API, Open-Meteo Weather API, and reads local sensor files.
*   `prompts/system_prompt.txt`: The persona and instructions for the AI.
*   `data/`: Contains sensor data files (`current_sensor.json` is the active one).

## License

[License Name]
