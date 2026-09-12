"""
config.py
Central configuration: environment variables, constants, feature flags.
Never hard-code secrets here — everything sensitive is read from .env.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# --- Database ---
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "health.db"))

# --- Groq AI ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))

# --- App ---
APP_NAME = "Smart Health Assistant"
APP_ICON_PATH = str(ASSETS_DIR / "health_icon.png")
APP_ICON = APP_ICON_PATH
MAX_UPLOAD_MB = 5
ALLOWED_IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]

GENDER_OPTIONS = ["Male", "Female", "Other", "Prefer not to say"]
COMMON_ALLERGENS = [
    "Peanuts", "Tree Nuts", "Milk/Dairy", "Eggs", "Soy", "Wheat/Gluten",
    "Fish", "Shellfish", "Sesame", "Mustard",
]

# --- Session ---
SESSION_KEYS = {
    "user_id": "user_id",
    "username": "username",
    "logged_in": "logged_in",
    "dark_mode": "dark_mode",
}

# --- Wellness defaults ---
DEFAULT_WATER_TARGET_ML = 2500
DEFAULT_SLEEP_TARGET_HOURS = 8.0

DIET_TYPES = ["Vegetarian", "Non-Vegetarian", "Eggetarian"]
ACTIVITY_LEVELS = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"]
FITNESS_LEVELS = ["Beginner", "Intermediate", "Advanced"]
HEALTH_GOALS = ["Weight Loss", "Weight Gain", "Weight Maintenance", "General Fitness", "Muscle Gain"]
MEAL_STYLES = ["Home-cooked", "Quick & Simple", "Traditional", "Mixed"]

DISCLAIMER = (
    "Smart Health Assistant — Your daily wellness companion for tracking health, nutrition, fitness, sleep and hydration."
)
