from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Configure API Keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Initialize ElevenLabs Client
eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER FUNCTIONS ---
def get_snowflake_conn():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        database="AI_COO_DB",
        schema="CORE_DATA"
    )

def get_snowflake_data():
    try:
        conn = get_snowflake_conn()
        cur = conn.cursor()
        cur.execute("SELECT region, SUM(revenue), SUM(tickets_opened) FROM company_sales GROUP BY region")
        rows = cur.fetchall()
        data_str = "Live Snowflake Data Summary:\n"
        for row in rows:
            data_str += f"- Region: {row[0]} | Total Revenue: ${row[1]} | Support Tickets: {row[2]}\n"
        conn.close()
        return data_str
    except Exception as e:
        return f"Data retrieval failed. Please upload data first. Error: {e}"

# ==========================================
# 🚀 UPGRADED FEATURE: FILE UPLOAD (CSV & JSON)
# ==========================================
@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check the file extension to decide how Pandas should read it
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif file.filename.endswith('.json'):
            df = pd.read_json(file.file)
        else:
            return {"error": "Unsupported file type. Please upload CSV or JSON."}
        
        # Standardize column names for Snowflake
        df.columns = [col.upper() for col in df.columns]

        # Push to Snowflake
        conn = get_snowflake_conn()
        success, nchunks, nrows, _ = write_pandas(conn, df, "COMPANY_SALES", auto_create_table=True, overwrite=True)
        conn.close()
        
        return {"message": f"Success! Uploaded {nrows} rows from {file.filename} to Snowflake."}
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}

# ==========================================
# 🚀 NEW FEATURE: POSTGRES DATABASE SYNC
# ==========================================
class PostgresSyncRequest(BaseModel):
    db_url: str  # Example: postgresql://user:password@localhost:5432/dbname

@app.post("/sync-postgres")
def sync_postgres(request: PostgresSyncRequest):
    try:
        # 1. Connect to the provided Postgres database
        engine = create_engine(request.db_url)
        
        # 2. Extract data (Assuming the table is named 'sales'. Adjust if needed!)
        # In a real app, you'd let the user type the table name too.
        query = "SELECT * FROM sales" 
        df = pd.read_sql(query, engine)
        
        # 3. Standardize for Snowflake
        df.columns = [col.upper() for col in df.columns]
        
        # 4. Push to Snowflake Data Warehouse
        conn = get_snowflake_conn()
        success, nchunks, nrows, _ = write_pandas(conn, df, "COMPANY_SALES", auto_create_table=True, overwrite=True)
        conn.close()
        
        return {"message": f"Success! Synced {nrows} rows from Postgres to Snowflake."}
    except Exception as e:
        return {"error": f"Postgres Sync failed: {str(e)}"}

# --- FEATURE: PODCAST (ElevenLabs Voice 1) ---
class PodcastRequest(BaseModel):
    extra_context: str = ""

@app.post("/generate-podcast")
def generate_podcast(request: PodcastRequest):
    live_data = get_snowflake_data()
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"Data: {live_data}\nWrite a 20-second professional CEO morning briefing."
    response = model.generate_content(prompt)
    script = response.text
    
    # Generate hyper-realistic audio using ElevenLabs
    audio = eleven_client.generate(text=script, voice="Marcus") # Marcus = Professional
    save(audio, "daily_podcast.mp3")
    
    return {"message": "Success", "script": script}

@app.get("/play-podcast")
def play_podcast():
    return FileResponse("daily_podcast.mp3", media_type="audio/mpeg")

# --- FEATURE: WAR ROOM (ElevenLabs Voice 2) ---
class AskRequest(BaseModel):
    question: str

@app.post("/ask-coo")
def ask_coo(request: AskRequest):
    live_data = get_snowflake_data()
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"Data: {live_data}\nCEO asks: {request.question}\nAnswer directly."
    response = model.generate_content(prompt)
    script = response.text
    
    # Generate audio using a different voice
    audio = eleven_client.generate(text=script, voice="Rachel") # Rachel = Calm, Analytical
    save(audio, "answer.mp3")
    
    return {"message": "Success", "answer": script, "math_used": live_data}

@app.get("/play-answer")
def play_answer():
    return FileResponse("answer.mp3", media_type="audio/mpeg")

# --- FEATURE: RISK RADAR (ElevenLabs Voice 3) ---
@app.post("/risk-radar")
def risk_radar():
    try:
        live_data = get_snowflake_data()
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        You are an autonomous Risk AI. Data: {live_data}
        Identify the biggest risk. Generate a 15-second URGENT warning script. 
        Start with "Critical Alert."
        """
        response = model.generate_content(prompt)
        script = response.text
        
        # Generate audio using an urgent/deep voice
        audio = eleven_client.generate(text=script, voice="Charlie") # Charlie = Deep, Authoritative
        save(audio, "alert.mp3")
        
        return {"alert_script": script}
    except Exception as e:
        return {"error": str(e)}

@app.get("/play-alert")
def play_alert():
    return FileResponse("alert.mp3", media_type="audio/mpeg")