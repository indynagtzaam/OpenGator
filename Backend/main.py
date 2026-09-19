from fastapi import FastAPI
from anthropic import Anthropic 
from dotenv import load_dotenv
import os 
from pydantic import BaseModel
from supabase import create_client

app = FastAPI()
load_dotenv()
client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
