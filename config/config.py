import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Config:
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")

        # LLM Configurations
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

        # Long Term Semantic Memory Configurations
        self.MEM0_API_KEY = os.getenv("MEM0_API_KEY")

        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Instancia global
settings = Config()
