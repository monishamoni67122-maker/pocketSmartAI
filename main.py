"""
PocketSmart AI - FastAPI Backend
Smart Budget & Recommendation Assistant powered by Gemini 1.5 Flash
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv

from models.schemas import (
    UserRegister, UserLogin, Token, UserResponse,
    HomePlannerRequest, PartyPlannerRequest, JewelryPlannerRequest,
    PlannerResponse, HomeItem, RoomType, EventType, StylePreference
)
from services import gemini_service, auth_service

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "PocketSmart AI")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

app = FastAPI(
    title=APP_NAME,
    description="GenAI-powered cross-platform budget recommendation system",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)


# ---------- Helpers ----------

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        return None
    payload = auth_service.decode_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    return auth_service.get_user_by_username(username)


def get_token_from_cookie_or_header(request: Request) -> Optional[str]:
    # Prefer Authorization header, fallback to cookie
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:]
    return request.cookies.get("access_token")


async def get_optional_user(request: Request):
    token = get_token_from_cookie_or_header(request)
    if not token:
        return None
    payload = auth_service.decode_token(token)
    if not payload:
        return None
    return auth_service.get_user_by_username(payload.get("sub"))


# ---------- Page Routes (HTML) ----------

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, user=Depends(get_optional_user)):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "app_name": APP_NAME,
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "user": None, "app_name": APP_NAME})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "user": None, "app_name": APP_NAME})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_optional_user)):
    if not user:
        return RedirectResponse("/login", status_code=302)
    history = auth_service.get_history(user["id"])
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "history": history[:10],
        "app_name": APP_NAME,
    })


@app.get("/planner/home", response_class=HTMLResponse)
async def home_planner_page(request: Request, user=Depends(get_optional_user)):
    return templates.TemplateResponse("home_planner.html", {
        "request": request, "user": user, "app_name": APP_NAME
    })


@app.get("/planner/party", response_class=HTMLResponse)
async def party_planner_page(request: Request, user=Depends(get_optional_user)):
    return templates.TemplateResponse("party_planner.html", {
        "request": request, "user": user, "app_name": APP_NAME
    })


@app.get("/planner/jewelry", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request, user=Depends(get_optional_user)):
    return templates.TemplateResponse("jewelry_planner.html", {
        "request": request, "user": user, "app_name": APP_NAME
    })


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user=Depends(get_optional_user)):
    if not user:
        return RedirectResponse("/login", status_code=302)
    history = auth_service.get_history(user["id"])
    return templates.TemplateResponse("history.html", {
        "request": request, "user": user, "history": history, "app_name": APP_NAME
    })


@app.get("/testimonials", response_class=HTMLResponse)
async def testimonials_page(request: Request, user=Depends(get_optional_user)):
    return templates.TemplateResponse("testimonials.html", {
        "request": request, "user": user, "app_name": APP_NAME
    })


# ---------- Auth API ----------

@app.post("/register")
async def register(user_data: UserRegister):
    try:
        user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return {"message": "Registration successful", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/token", response_model=Token)
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = auth_service.create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/login")
async def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = auth_service.authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "user": None,
            "error": "Invalid username or password",
            "app_name": APP_NAME,
        }, status_code=401)
    token = auth_service.create_access_token(data={"sub": user["username"]})
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )
    return response


@app.post("/api/login")
async def api_login(credentials: UserLogin):
    user = auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = auth_service.create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.get("/session-info")
async def session_info(user=Depends(get_optional_user)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


# ---------- Recommendation APIs ----------

@app.post("/generate-home")
async def generate_home(
    request: Request,
    budget: float = Form(...),
    rooms: str = Form(...),           # comma-separated
    items_json: str = Form("[]"),     # JSON string of items
    style: str = Form("modern"),
    platforms: str = Form("Amazon,Flipkart,IKEA"),
    notes: str = Form(""),
    user=Depends(get_optional_user),
):
    import json
    try:
        items = json.loads(items_json) if items_json else []
    except json.JSONDecodeError:
        items = []

    room_list = [r.strip() for r in rooms.split(",") if r.strip()]
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]

    data = {
        "budget": budget,
        "rooms": room_list,
        "items": items,
        "style": style,
        "preferred_platforms": platform_list,
        "additional_notes": notes,
    }
    result = gemini_service.generate_home_recommendations(data)

    if user:
        auth_service.add_to_history(user["id"], {
            "type": "home",
            "input": data,
            "result_summary": result.get("summary", ""),
            "total_budget": budget,
        })

    # If request wants HTML (form submit) render results page
    accept = request.headers.get("accept", "")
    if "text/html" in accept or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return templates.TemplateResponse("results.html", {
            "request": request,
            "user": user,
            "result": result,
            "planner_type": "home",
            "app_name": APP_NAME,
        })
    return JSONResponse(result)


@app.post("/api/generate-home")
async def api_generate_home(body: HomePlannerRequest, user=Depends(get_optional_user)):
    data = body.model_dump()
    # Convert enums
    data["rooms"] = [r.value if hasattr(r, "value") else r for r in data["rooms"]]
    data["items"] = [
        {**item, "preferred_style": item["preferred_style"].value if hasattr(item.get("preferred_style"), "value") else item.get("preferred_style")}
        for item in data.get("items", [])
    ]
    if data.get("style") and hasattr(data["style"], "value"):
        data["style"] = data["style"].value
    result = gemini_service.generate_home_recommendations(data)
    if user:
        auth_service.add_to_history(user["id"], {
            "type": "home",
            "input": data,
            "result_summary": result.get("summary", ""),
            "total_budget": body.budget,
        })
    return result


@app.post("/generate-party")
async def generate_party(
    request: Request,
    budget: float = Form(...),
    guest_count: int = Form(...),
    event_type: str = Form(...),
    venue_preference: str = Form(""),
    city: str = Form("Mumbai"),
    platforms: str = Form("Swiggy,Zomato,OYO,Amazon"),
    notes: str = Form(""),
    user=Depends(get_optional_user),
):
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    data = {
        "budget": budget,
        "guest_count": guest_count,
        "event_type": event_type,
        "venue_preference": venue_preference or None,
        "city": city,
        "preferred_platforms": platform_list,
        "additional_notes": notes,
    }
    result = gemini_service.generate_party_recommendations(data)
    if user:
        auth_service.add_to_history(user["id"], {
            "type": "party",
            "input": data,
            "result_summary": result.get("summary", ""),
            "total_budget": budget,
        })
    accept = request.headers.get("accept", "")
    if "text/html" in accept or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return templates.TemplateResponse("results.html", {
            "request": request,
            "user": user,
            "result": result,
            "planner_type": "party",
            "app_name": APP_NAME,
        })
    return JSONResponse(result)


@app.post("/api/generate-party")
async def api_generate_party(body: PartyPlannerRequest, user=Depends(get_optional_user)):
    data = body.model_dump()
    if data.get("event_type") and hasattr(data["event_type"], "value"):
        data["event_type"] = data["event_type"].value
    result = gemini_service.generate_party_recommendations(data)
    if user:
        auth_service.add_to_history(user["id"], {
            "type": "party",
            "input": data,
            "result_summary": result.get("summary", ""),
            "total_budget": body.budget,
        })
    return result


@app.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form("contemporary"),
    metal_preference: str = Form(""),
    platforms: str = Form("Amazon,Flipkart"),
    notes: str = Form(""),
    outfit_image: Optional[UploadFile] = File(None),
    user=Depends(get_optional_user),
):
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "metal_preference": metal_preference or None,
        "preferred_platforms": platform_list,
        "additional_notes": notes,
    }
    image_bytes = None
    mime = "image/jpeg"
    if outfit_image and outfit_image.filename:
        image_bytes = await outfit_image.read()
        mime = outfit_image.content_type or "image/jpeg"

    result = gemini_service.generate_jewelry_recommendations(data, image_bytes, mime)
    if user:
        auth_service.add_to_history(user["id"], {
            "type": "jewelry",
            "input": {k: v for k, v in data.items()},
            "result_summary": result.get("summary", ""),
            "total_budget": budget,
            "had_image": bool(image_bytes),
        })
    accept = request.headers.get("accept", "")
    if "text/html" in accept or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return templates.TemplateResponse("results.html", {
            "request": request,
            "user": user,
            "result": result,
            "planner_type": "jewelry",
            "app_name": APP_NAME,
        })
    return JSONResponse(result)


@app.post("/api/generate-jewelry")
async def api_generate_jewelry(
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form("contemporary"),
    metal_preference: str = Form(""),
    platforms: str = Form("Amazon,Flipkart"),
    notes: str = Form(""),
    outfit_image: Optional[UploadFile] = File(None),
    user=Depends(get_optional_user),
):
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "metal_preference": metal_preference or None,
        "preferred_platforms": platform_list,
        "additional_notes": notes,
    }
    image_bytes = None
    mime = "image/jpeg"
    if outfit_image and outfit_image.filename:
        image_bytes = await outfit_image.read()
        mime = outfit_image.content_type or "image/jpeg"
    result = gemini_service.generate_jewelry_recommendations(data, image_bytes, mime)
    if user:
        auth_service.add_to_history(user["id"], {
            "type": "jewelry",
            "input": data,
            "result_summary": result.get("summary", ""),
            "total_budget": budget,
            "had_image": bool(image_bytes),
        })
    return result


@app.get("/api/history")
async def api_history(user=Depends(get_optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return auth_service.get_history(user["id"])


@app.get("/health")
async def health():
    has_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "ok",
        "app": APP_NAME,
        "gemini_configured": has_key,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=DEBUG)
