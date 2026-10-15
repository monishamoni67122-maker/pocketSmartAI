# PocketSmart AI — Smart Budget & Recommendation Assistant

**PocketSmart AI** is a GenAI-powered, cross-platform recommendation system that delivers personalized, budget-based suggestions for:

- 🏠 **Home Interiors** (furniture, lighting, decor) — Amazon, Flipkart, IKEA  
- 🎉 **Party Planning** (catering, decoration, venue) — Swiggy, Zomato, OYO  
- 💍 **Jewelry** (occasion & style matched, optional outfit image) — Amazon, Flipkart  

Powered by **Google Gemini 1.5 Flash** and built with **FastAPI** + Jinja2 templates.

---

## Features

- Three dedicated budget planners with smart allocation  
- Multimodal support (text + optional outfit image for jewelry)  
- User registration / login (JWT + cookie sessions)  
- Recommendation history for logged-in users  
- Graceful fallback demo recommendations when Gemini API key is missing  
- Responsive dark-themed UI  

---

## Project Structure

```
PocketSmartAI/
├── main.py                 # FastAPI application entry point
├── requirements.txt
├── .env.example            # Copy to .env and fill values
├── README.md
├── models/
│   └── schemas.py          # Pydantic request/response models
├── services/
│   ├── gemini_service.py   # Gemini prompts & recommendation logic
│   └── auth_service.py     # In-memory auth + history
├── templates/              # Jinja2 HTML pages
│   ├── base.html
│   ├── index.html
│   ├── login.html / register.html
│   ├── dashboard.html / history.html
│   ├── home_planner.html / party_planner.html / jewelry_planner.html
│   ├── results.html
│   └── testimonials.html
└── static/
    ├── css/style.css
    └── js/app.js
```

---

## Prerequisites

- Python **3.10+** (3.11 or 3.12 recommended)
- A Google AI Studio / Gemini API key (optional but recommended)  
  → Get one free at: https://aistudio.google.com/app/apikey

---

## Quick Start (Run Instructions)

### 1. Unzip the project

```bash
unzip PocketSmartAI.zip
cd PocketSmartAI
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Copy example env file
# Windows (Command Prompt):
copy .env.example .env

# Windows (PowerShell) / macOS / Linux:
cp .env.example .env

# Edit .env and set your Gemini API key:
# GEMINI_API_KEY=your_actual_key_here
```

> **Note:** If `GEMINI_API_KEY` is empty or invalid, the app still runs and returns realistic **demo/fallback** recommendations so you can explore the full UI.

### 5. Start the server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Open in browser

```
http://localhost:8000
```

---

## Demo Login

| Field    | Value      |
|----------|------------|
| Username | `demo`     |
| Password | `demo123`  |

You can also register a new account from the Sign Up page.

---

## API Endpoints (summary)

| Method | Path                 | Description                          |
|--------|----------------------|--------------------------------------|
| GET    | `/`                  | Landing page                         |
| GET    | `/planner/home`      | Home interior planner form           |
| GET    | `/planner/party`     | Party planner form                   |
| GET    | `/planner/jewelry`   | Jewelry planner form                 |
| POST   | `/generate-home`     | Generate home recommendations        |
| POST   | `/generate-party`    | Generate party recommendations       |
| POST   | `/generate-jewelry`  | Generate jewelry recommendations     |
| POST   | `/register`          | Register new user (JSON)             |
| POST   | `/login`             | Form login → sets cookie             |
| POST   | `/token`             | OAuth2 token (for API clients)       |
| GET    | `/dashboard`         | User dashboard (auth required)       |
| GET    | `/history`           | Recommendation history               |
| GET    | `/health`            | Health check + Gemini status         |
| GET    | `/docs`              | Interactive Swagger UI               |

JSON API variants also available under `/api/generate-*`.

---

## Testing the Planners

1. **Home** — Budget ₹50,000–1,00,000, select rooms, add items (sofa, lights…), submit.  
2. **Party** — Budget ₹20,000+, guest count, event type (birthday/wedding…), submit.  
3. **Jewelry** — Budget ₹5,000+, occasion, optional outfit image upload, submit.

Results show category-wise budget allocation, product cards with platform links, and tips.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure venv is activated and `pip install -r requirements.txt` succeeded |
| Gemini errors / fallback banner | Check `GEMINI_API_KEY` in `.env`; restart server after changing |
| Port already in use | Change `PORT=8001` in `.env` or use `--port 8001` |
| Image upload fails | Ensure Pillow is installed; use JPG/PNG under ~5 MB |
| bcrypt / passlib warning | Already pinned compatible versions in `requirements.txt` |

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Pydantic, python-jose, passlib  
- **AI:** Google Generative AI (`google-generativeai`) — Gemini 1.5 Flash  
- **Frontend:** HTML5, CSS3, Vanilla JS, Jinja2  
- **Auth:** JWT (cookie + Bearer) with in-memory user store (demo)  

---

## License

This project is provided as an educational / portfolio example.  
Replace the in-memory auth store with a real database before production use.

---

**PocketSmart AI** — Plan Smart. Spend Wise.
