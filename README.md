# Smart Health Assistant

A responsive, AI-powered health & wellness assistant built with Python and Streamlit — for educational/college-project use.

> **Disclaimer:** Smart Health Assistant provides general wellness information for educational purposes only. It is **not** a medical device and does **not** diagnose, treat, or prescribe. It does not replace a qualified doctor or healthcare professional. For medical concerns or emergencies, seek appropriate professional care.

---

## 1. Overview

Smart Health Assistant helps users track health data (weight, BMI, water, sleep, exercise), understand wellness trends via an AI-assisted Health Score, get personalized food and diet recommendations that respect dietary restrictions and allergies, generate recipes from available ingredients, analyze meal photos, plan workouts, set medicine reminders, and chat with an AI wellness assistant — all backed by a real SQLite database, with weekly PDF reports.

## 2. Features

**Authentication & Profile**
- Secure registration/login/logout (PBKDF2-HMAC-SHA256 password hashing, per-user salt, no plain-text passwords)
- Full editable profile: demographics, activity/fitness level, health goal, diet type, food preferences, allergies, budget, sleep/water targets

**Dashboard & Health Tracking**
- Unified dashboard: Health Score, BMI, weight, water/sleep/exercise/food summaries — all from real DB records, never hard-coded
- BMI calculator + weight history & trend chart
- BMR / TDEE / goal-calorie estimator (clearly labeled as estimates)
- AI-flavored **Health Score** (0–100) combining BMI, weight trend, water, sleep, activity, and food quality — explicitly non-diagnostic
- Water tracker (daily target, logging, weekly chart)
- Sleep analyzer (duration, quality, weekly trend, general suggestions — no disorder diagnosis)
- Exercise planner (goal/fitness/time-aware suggestions with professional-guidance cautions)

**Food Intelligence** (the project's signature feature)
- Deterministic, rule-based recommendation engine covering Fruits, Vegetables, Dal, Pulses, Beans, Chickpeas, Rajma, Grains, Millets, Nuts, Seeds, Dairy, Eggs, Veg/Non-veg foods, and Healthy snacks
- **Diet-type and allergy filtering is enforced twice**: once in the deterministic catalog, and again as a guardrail applied to every AI-generated food/recipe list — so a vegetarian or allergic user is protected even if the AI slips
- Personalized diet plan (breakfast/mid-morning/lunch/evening/dinner)
- Budget-aware meal planning with an approximate-cost disclaimer
- "What Can I Cook?" — ingredient-to-recipe generator
- Healthy Recipe Generator — personalized recipe for any food name
- "Make My Food Healthier" — practical improvements for familiar foods, not just "don't eat it"
- AI Meal Analyzer — upload a food photo for identification, approximate nutrition, and healthier alternatives (clearly labeled as an estimate)
- Food Score (variety, balance, portion awareness, processed-food frequency)

**AI Assistant**
- Text + voice chat (voice degrades gracefully to text-only if the microphone/library is unavailable)
- Per-user, persistent chat history with a clear-history option
- All AI calls go through one service layer (`services/ai_client.py`) with typed errors, timeouts, and retries — no feature file talks to the Groq API directly
- Structured prompt templates per feature (`services/prompts/`) — the AI is only given the user's real, stored data and is instructed to say "unavailable" rather than invent facts

**Medicine Reminders**
- Name, time, frequency, notes, enable/disable — reminder-only, never a prescribing or diagnostic feature

**Analytics & Reports**
- Interactive Plotly charts for weight, BMI, water, sleep, calories, food score, health score, and activity
- Weekly AI Health Report assembled from real tracked data, exported as a professional PDF (ReportLab) with report history and re-download

**Other**
- Dark mode, responsive desktop/tablet/mobile layout, reusable UI components (metric cards, alerts, progress bars, AI/food/recipe cards, empty/loading/error states)

## 3. Technology Stack

Python · Streamlit · SQLite · Pandas · NumPy · Pillow · Plotly · ReportLab · Groq API · python-dotenv · custom CSS

## 4. Architecture

```
Presentation  → pages/*.py (Streamlit multipage) + ui/ (theme, reusable components, CSS)
Application   → core/ (auth, health calculations, food/recipe/exercise/sleep/water logic,
                 meal analyzer, report generator, voice assistant, utils)
Service       → services/ai_client.py (the only file that calls Groq) +
                 services/prompts/ (reusable, structured prompt templates)
Data          → core/database.py (schema init + parameterized CRUD "repository" functions)
                 → data/health.db (SQLite)
```

Key design decisions:
- **Deterministic-first food safety.** Diet type and allergy filtering happen in plain Python (`core/food_ai.py`), before *and* after any AI call — never left solely to the model.
- **Single AI gateway.** Only `services/ai_client.py` imports the Groq SDK. Every feature calls through it, so timeouts, retries, and error handling are consistent everywhere.
- **`UserContext`** is assembled once per request straight from the database and is the only "facts" source handed to prompts, so the AI can't invent user data.
- **No monolith files.** Each concern lives in its own module under `core/`, `services/`, or `ui/`.

## 5. Folder Structure

```
Smart_Health_Assistant/
├── app.py                     # Entry point: auth gate + dashboard
├── config.py                  # Env vars, constants, feature flags
├── requirements.txt
├── .env.example
├── .gitignore
│
├── core/
│   ├── auth.py                # register/login/logout/session, password hashing
│   ├── database.py            # schema init + all CRUD (parameterized SQL only)
│   ├── models.py              # UserProfile / UserContext dataclasses
│   ├── health_calculations.py # BMI, BMR, TDEE, Health Score, Food Score
│   ├── food_ai.py             # deterministic + AI-personalized food engine
│   ├── recipe_ai.py           # what-can-I-cook / healthy recipe / make-it-healthier
│   ├── meal_analyzer.py       # AI food-image analysis
│   ├── exercise_ai.py         # exercise plan generator
│   ├── sleep_analyzer.py      # sleep summary + trend logic
│   ├── water_tracker.py       # water CRUD + progress logic
│   ├── report_generator.py    # weekly summary + PDF (ReportLab)
│   ├── voice_assistant.py     # speech input wrapper with text fallback
│   └── utils.py                # validators, formatters, file-safety checks
│
├── services/
│   ├── ai_client.py            # Groq wrapper: timeouts, retries, typed errors
│   └── prompts/                # food / recipe / meal-analysis / exercise / chat / report prompts
│
├── ui/
│   ├── components.py           # metric_card, alert, progress_bar, ai/food/recipe cards, states
│   ├── theme.py                 # color tokens + icon map
│   └── styles.css               # responsive breakpoints (desktop/tablet/mobile)
│
├── pages/                      # Streamlit native multipage navigation
│   ├── 1_Profile.py … 10_Settings.py
│
├── assets/
│   └── health_icon.png         # favicon
├── data/                       # health.db (created on first run, gitignored)
├── reports/                    # generated PDF reports (gitignored)
└── tests/                      # unit tests
```

## 6. Installation

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com) (optional for browsing the app, required for AI features)

### Steps

```bash
# 1. Clone / unzip the project, then enter the folder
cd Smart_Health_Assistant

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then open .env and paste your real GROQ_API_KEY

# 5. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. The SQLite database is created automatically on first run at `data/health.db` — existing data is never wiped on restart.

### Environment variables (`.env`)

| Variable | Purpose | Required |
|---|---|---|
| `GROQ_API_KEY` | Enables all AI features (chat, recommendations, meal analysis, reports) | Optional — app runs without it, AI features show a friendly "not configured" message |
| `GROQ_TEXT_MODEL` | Text model name | No (has a default) |
| `GROQ_VISION_MODEL` | Vision model for meal photo analysis | No (has a default) |
| `DB_PATH` | SQLite file location | No (defaults to `data/health.db`) |

## 7. Running Tests

```bash
pytest tests/
```

## 8. Troubleshooting

- **"AI assistant is not configured"** — set a real `GROQ_API_KEY` in `.env` and restart the app.
- **"database is locked"** — avoid running two `streamlit run` instances against the same `data/health.db` simultaneously.
- **Voice input doesn't respond** — the app falls back to text automatically if microphone access or `SpeechRecognition` isn't available in your environment; text chat still works fully.
- **Mobile layout looks off in an embedded preview** — test in an actual mobile browser tab; some embedded/iframe previews constrain viewport width differently than a real device.

## 9. Screenshots

_Add screenshots here after running the app locally: Dashboard, Food Intelligence, Meal Analyzer, Weekly Report PDF, Mobile view._

## 10. Future Enhancements

- Wearable/device sync (steps, heart rate) for a more accurate Health Score
- Multi-language support for food recommendations and recipes
- Push/email notifications for medicine reminders
- Barcode-based packaged-food nutrition lookup
- Exportable CSV of full historical data

## 11. Safety Disclaimer

This application is a wellness/educational tool, not a medical diagnostic system. It never diagnoses conditions, prescribes or adjusts medication, or guarantees health outcomes. The Health Score and Food Score are general wellness indicators, not clinically validated metrics. Medicine reminders are scheduling aids only. For any medical concern, symptom, or emergency, consult a qualified healthcare professional or emergency services.

## 12. UI/UX Redesign Notes

The interface was redesigned into a cohesive, app-like design system without touching backend/database/AI logic:

- **Navigation**: sidebar now uses Streamlit's `st.navigation`/`st.Page` API with friendly titles and icons ("Dashboard" first, not "app"), a proper logo slot via `st.logo()`, and a mini user-profile + logout pinned to the bottom.
- **Design system**: `ui/theme.py` + `ui/styles.css` define CSS variables for light and dark mode (navy/teal health-tech palette), a typography scale, consistent icon badges, cards, badges, chat bubbles, and full responsive breakpoints (desktop/tablet/mobile). `.streamlit/config.toml` sets the base Streamlit theme to match.
- **Dashboard**: personalized greeting, metric cards with trend indicators, quick-action buttons, and a real 2×2 analytics grid (weight/water/health-score/food-score) — all from live database data, with proper empty states instead of blank space.
- **No more raw data**: `Settings.py`'s raw JSON dump and `Exercise.py`'s raw fallback dump were replaced with clean label/value info panels and the same structured plan renderer used for AI output.
- **Multi-widget cards**: any card containing more than one real Streamlit widget (charts, forms) uses `ui.card_container()` (an `st.container(key=...)` wrapper), not a raw opened/closed `<div>` — Streamlit does not nest content inside HTML tags split across separate `st.markdown()` calls, since each call renders as an independent DOM sibling.
- **HTML rendering rule**: every component in `ui/components.py` builds its HTML as a single-line string. Streamlit's markdown renderer follows CommonMark, where a blank line followed by 4+ spaces of indentation is parsed as a code block — a "pretty," indented multi-line f-string with an empty conditional interpolation can silently render as literal escaped text. Keep this in mind if you add new HTML-producing components.
