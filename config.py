import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///job_course.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    REQUEST_TIMEOUT = 10

    SIMILARITY_THRESHOLD = 0.3
    MAX_RECOMMENDATIONS = 10