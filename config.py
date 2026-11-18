# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sports-genomics-super-secret")
    
    # MySQL Database Connection (SQLAlchemy)
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASS = os.environ.get("DB_PASS", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME", "sports_genomics_db")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Meta / Facebook Messenger
    VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_sports_verify_token")
    DEFAULT_PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # OpenAI API Key
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")