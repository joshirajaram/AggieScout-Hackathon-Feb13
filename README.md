# AggieScout

Telegram bot + Gemini backend for agricultural alerts (frost/heat/normal) and optional multi-agent council.

## Prerequisites

- Python 3.9+
- [Telegram Bot Token](https://t.me/BotFather) (for the bot)
- [Gemini API Key](https://ai.google.dev/) (for LLM alerts)

## Setup

```bash
cd AggieScout
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

The Telegram token is currently set in `bot.py`; you can replace it or move it to `.env` and load with `os.getenv("TELEGRAM_BOT_TOKEN")`.

## How to run

### 1. Telegram bot (main app)

Starts the bot so users can message it and get alerts:

```bash
python bot.py
```

Then open your bot in Telegram, send **Start**, and type a question (e.g. “What should I do right now?”). The bot uses `data/frost_sensor.json` by default and returns Gemini mitigation text (or fallback if no API key).

### 2. Alert engine only (CLI, no Telegram)

Run the alert pipeline once and print the result:

```bash
python llm_engine.py              # default: frost scenario
python llm_engine.py frost
python llm_engine.py heat
python llm_engine.py normal
```

Uses `data/{frost|heat|normal}_sensor.json` and `prompts/system_prompt.txt`.

### 3. Council (multi-agent: Agronomist → Weather → Foreman)

Runs three sequential Gemini calls and prints a combined report (no Telegram):

```bash
python council_engine.py
```

Uses `data/weather_mock_data.json` for the Weather Node. Optional: pass an image by calling `run_council(user_text, image_bytes)` from code.

## Project layout

| Path | Purpose |
|------|--------|
| `bot.py` | Telegram entry point; calls `generate_alert_async()` from llm_engine |
| `llm_engine.py` | Builds prompt from sensor + system prompt, calls Gemini or fallback |
| `council_engine.py` | Standalone 3-agent pipeline (Agronomist / Weather / Foreman) |
| `prompts/system_prompt.txt` | AggieScout rules and response format for the LLM |
| `data/frost_sensor.json` | Mock frost readings (used by default for bot) |
| `data/heat_sensor.json` | Mock heat readings |
| `data/normal_sensor.json` | Mock normal readings |
| `data/weather_mock_data.json` | Weather context for council_engine |

## License

Apache-2.0
