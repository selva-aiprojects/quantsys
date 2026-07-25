from fastapi import FastAPI, Request, Response, HTTPException, Cookie, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import os
import json
import time
import secrets
from typing import Optional, Dict
from google import genai
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_auth_requests
from google.auth import exceptions as google_auth_exceptions
from dotenv import load_dotenv

load_dotenv()

# Cookies with Secure=True are silently dropped by browsers over plain HTTP
# (e.g. http://localhost:8000). Only require HTTPS-only cookies in production.
IS_PROD = os.getenv("VERCEL") == "1" or os.getenv("ENV", "").lower() == "production"

app = FastAPI(title="QuantSys AI Portfolio API")

# IMPORTANT: allow_credentials + allow_origins=["*"] is not a valid combination
# for browsers (cookies won't be sent), so we echo back the requesting origin
# instead. Set ALLOWED_ORIGINS env var (comma-separated) in production.
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_origin_regex=None if allowed_origins else ".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Google Sign-In configuration ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
_google_auth_request = google_auth_requests.Request()

# Simple in-memory session store: session_id -> {email, name, picture, exp}
# NOTE: this resets on server restart / cold start (e.g. on Vercel serverless).
# For a persistent multi-instance deployment, swap this for Redis/DB-backed
# sessions or, more simply, a signed JWT stored in the cookie itself.
_sessions: Dict[str, dict] = {}
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


class GoogleAuthRequest(BaseModel):
    credential: str  # the ID token (JWT) returned by Google Identity Services


def _create_session(user: dict) -> str:
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {**user, "exp": time.time() + SESSION_TTL_SECONDS}
    return session_id


def _get_session_user(session_id: Optional[str]) -> Optional[dict]:
    if not session_id:
        return None
    session = _sessions.get(session_id)
    if not session:
        return None
    if session["exp"] < time.time():
        _sessions.pop(session_id, None)
        return None
    return session

app.mount("/static", StaticFiles(directory="static"), name="static")

class PortfolioRequest(BaseModel):
    amount: float
    risk: str
    sectors: list[str]

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    # Inject the real Google OAuth client ID at request time so it never
    # has to be hardcoded in the static HTML file.
    return html.replace("__GOOGLE_CLIENT_ID__", GOOGLE_CLIENT_ID)


@app.post("/api/auth/google")
def google_login(payload: GoogleAuthRequest, response: Response):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is not set on the server. Please set it in your .env file.",
        )

    try:
        info = google_id_token.verify_oauth2_token(
            payload.credential, _google_auth_request, GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        # Malformed token, bad signature, audience/issuer mismatch, expired, etc.
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
    except google_auth_exceptions.GoogleAuthError as e:
        # e.g. couldn't fetch Google's signing certs (network/DNS issue on the
        # server). This is a server-side problem, not a bad client token.
        raise HTTPException(
            status_code=503,
            detail=f"Could not verify token with Google right now: {e}",
        )

    # Belt-and-suspenders check even though verify_oauth2_token already
    # validates the issuer.
    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    user = {
        "email": info.get("email"),
        "name": info.get("name"),
        "given_name": info.get("given_name"),
        "picture": info.get("picture"),
        "email_verified": info.get("email_verified", False),
    }

    session_id = _create_session(user)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=IS_PROD,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
    )
    return {"user": user}


def get_current_user(session_id: Optional[str] = Cookie(default=None)) -> dict:
    user = _get_session_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@app.get("/api/auth/me")
def auth_me(user: dict = Depends(get_current_user)):
    return {"user": {k: v for k, v in user.items() if k != "exp"}}


@app.post("/api/auth/logout")
def logout(response: Response, session_id: Optional[str] = Cookie(default=None)):
    if session_id:
        _sessions.pop(session_id, None)
    response.delete_cookie("session_id")
    return {"ok": True}

@app.get("/api/market-data")
def get_market_data(tickers: str, user: dict = Depends(get_current_user)):
    """
    Fetch market data for a comma-separated list of tickers.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {"error": "No tickers provided"}

    data = {}
    try:
        df = yf.download(ticker_list, period="5d", progress=False)
        
        for ticker in ticker_list:
            ticker_obj = yf.Ticker(ticker)
            try:
                # Handle single ticker or multiple ticker df structure
                if len(ticker_list) == 1:
                    close_series = df['Close']
                else:
                    close_series = df['Close'][ticker]
                
                # Check if series is empty
                if close_series.empty:
                    price = 0
                else:
                    price = float(close_series.dropna().iloc[-1])
                
                info = ticker_obj.info if ticker_obj.info else {}
                data[ticker] = {
                    "price": price,
                    "beta": info.get("beta", 1.0),
                    "sector": info.get("sector", "Unknown"),
                    "marketCap": info.get("marketCap", 0)
                }
            except Exception as e:
                data[ticker] = {"price": 0, "error": str(e)}
                
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/ai-predict")
def ai_predict(req: PortfolioRequest, user: dict = Depends(get_current_user)):
    if not client:
        return {"error": "GEMINI_API_KEY is not set. Please set it in .env file."}
    
    prompt = f"""
    You are an expert AI quantitative analyst and portfolio manager. 
    The user wants to invest {req.amount} INR.
    Their risk profile is: {req.risk}.
    They are interested in the following sectors: {', '.join(req.sectors) if req.sectors else 'All sectors'}.
    
    Please provide:
    1. Market and sector based analysis for the selected sectors.
    2. Any general guidance or outlook from corporates in these sectors (summarized).
    3. Your predictions and recommended allocation strategy based on historical performance and volatility.
    
    Return the response strictly as a JSON object with the following keys:
    {{
        "market_analysis": "string detailing the sector analysis",
        "corporate_guidance": "string detailing corporate guidance",
        "predictions": "string detailing your predictions and strategy",
        "recommended_allocation": [
             {{"ticker": "RELIANCE.NS", "sector": "Energy", "allocation_pct": 20, "reason": "..."}}
        ]
    }}
    Ensure the sum of allocation_pct equals 100. Provide indian tickers (e.g., .NS suffix) if appropriate or global ones if sectors suggest it. The output MUST be valid JSON.
    """
    
    models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash']
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text.strip())
        except Exception as e:
            last_error = e
            err_str = str(e)
            if any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded", "404", "NOT_FOUND"]):
                continue
            else:
                break

    err_str = str(last_error) if last_error else "Unknown error"
    if any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded"]):
        return {"error": "Gemini API free tier rate limit reached (20 requests/day). Please wait 30 seconds and try again."}
    return {"error": f"AI prediction failed: {err_str}"}