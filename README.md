```markdown
# 🧠 AI-COO Backend

This is the Python FastAPI backend for the AI-COO platform. It handles all AI orchestration, data ingestion into Snowflake, and text-to-speech generation via ElevenLabs.

## 🛠️ Tech Stack
* **API Framework:** FastAPI & Uvicorn
* **LLM Engine:** Google Generative AI (`google-generativeai` for Gemini 1.5 Pro/Flash)
* **Data Cloud:** Snowflake Cortex & Snowpark (`snowflake-snowpark-python`)
* **Voice Synthesis:** ElevenLabs (`elevenlabs`)
* **Task Scheduling:** APScheduler (for nightly podcast generation)

## ⚙️ Quick Start

### 1. Virtual Environment & Dependencies
It is highly recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: `venv\Scripts\activate`
pip install -r requirements.txt

Create a .env file in the root of the backend directory. Never commit this file.


# AI Services
GEMINI_API_KEY="your_google_ai_studio_key"
ELEVENLABS_API_KEY="your_elevenlabs_api_key"

# Snowflake Connection Details
SNOWFLAKE_ACCOUNT="your_account_identifier"
SNOWFLAKE_USER="your_username"
SNOWFLAKE_PASSWORD="your_password"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="AI_COO_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="ACCOUNTADMIN"

uvicorn main:app --reload --port 8000

The API will be available at http://localhost:8000.
