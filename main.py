from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import os
import json
import pandas as pd
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth


load_dotenv()

app = FastAPI(title="QuantSys AI Portfolio API")

# Load FinBERT Pipeline
try:
    from transformers import pipeline
    print("Loading FinBERT model...")
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    print("FinBERT loaded successfully.")
except Exception as e:
    sentiment_pipeline = None
    print(f"Failed to load FinBERT: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/api/firebase-config")
def get_firebase_config():
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
    }



# Database Setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nivesh.db")
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Firebase setup
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
if not firebase_admin._apps and FIREBASE_PROJECT_ID:
    firebase_admin.initialize_app(options={'projectId': FIREBASE_PROJECT_ID})


if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    portfolios = relationship("Portfolio", back_populates="owner")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    data = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="portfolios")

Base.metadata.create_all(bind=engine)

# Auth Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = token
    if token.startswith("user:"):
        username = token.replace("user:", "", 1)
    
    if "." in username:
        try:
            import jwt
            payload = jwt.decode(username, options={"verify_signature": False})
            username = payload.get("email") or payload.get("sub") or username
        except Exception:
            pass

    if not username:
        raise HTTPException(status_code=401, detail="Invalid identity token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

class UserCreate(BaseModel):
    username: str
    password: str

class PortfolioCreate(BaseModel):
    id: str
    name: str
    created_at: str
    history: list

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}


@app.get("/api/portfolios")
def get_portfolios(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).filter(Portfolio.owner_id == current_user.id).all()
    results = []
    for p in portfolios:
        results.append({
            "id": p.id,
            "name": p.name,
            "createdAt": p.created_at.isoformat() + "Z",
            "history": json.loads(p.data)
        })
    return results

@app.post("/api/portfolios")
def save_portfolio(p_req: PortfolioCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Portfolio).filter(Portfolio.id == p_req.id, Portfolio.owner_id == current_user.id).first()
    dt_str = p_req.created_at.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        dt = datetime.utcnow()
        
    if existing:
        existing.name = p_req.name
        existing.data = json.dumps(p_req.history)
    else:
        new_p = Portfolio(
            id=p_req.id,
            name=p_req.name,
            created_at=dt,
            data=json.dumps(p_req.history),
            owner_id=current_user.id
        )
        db.add(new_p)
    db.commit()
    return {"status": "success"}

@app.delete("/api/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"status": "success"}



class PortfolioRequest(BaseModel):
    amount: float
    risk: str
    sectors: list[str]
    volume_data: dict = {}
    rsi_data: dict = {}

class SentimentRequest(BaseModel):
    tickers: list[str]


# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/market-data")
def get_market_data(tickers: str, current_user: User = Depends(get_current_user)):
    """
    Fetch market data for a comma-separated list of tickers.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {"error": "No tickers provided"}

    data = {}
    try:
        # Fetch 60 days of data to accurately calculate 14-day RSI and 30-day avg volume
        df = yf.download(ticker_list, period="60d", progress=False)
        
        for ticker in ticker_list:
            ticker_obj = yf.Ticker(ticker)
            try:
                # Handle single ticker or multiple ticker df structure
                if len(ticker_list) == 1:
                    close_series = df['Close']
                    vol_series = df['Volume']
                else:
                    close_series = df['Close'][ticker]
                    vol_series = df['Volume'][ticker]
                
                # Check if series is empty
                if close_series.empty or vol_series.empty:
                    price = 0
                    rsi = 50
                    current_vol = 0
                    avg_vol = 0
                else:
                    close_series_clean = close_series.dropna()
                    vol_series_clean = vol_series.dropna()
                    
                    price = float(close_series_clean.iloc[-1])
                    
                    rsi_series = calculate_rsi(close_series_clean)
                    rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty and pd.notna(rsi_series.iloc[-1]) else 50
                    
                    current_vol = float(vol_series_clean.iloc[-1])
                    avg_vol = float(vol_series_clean.tail(30).mean())
                
                info = ticker_obj.info if ticker_obj.info else {}
                data[ticker] = {
                    "price": price,
                    "beta": info.get("beta", 1.0),
                    "sector": info.get("sector", "Unknown"),
                    "marketCap": info.get("marketCap", 0),
                    "rsi": round(rsi, 2),
                    "currentVolume": current_vol,
                    "averageVolume": avg_vol
                }
            except Exception as e:
                data[ticker] = {"price": 0, "error": str(e)}
                
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/sentiment-analysis")
def analyze_sentiment(req: SentimentRequest, current_user: User = Depends(get_current_user)):
    if not sentiment_pipeline:
        return {"error": "FinBERT model is not loaded."}
    
    results = {}
    for ticker in req.tickers:
        ticker_obj = yf.Ticker(ticker)
        news = ticker_obj.news
        if not news:
            results[ticker] = {"overall": "Neutral", "details": [], "corporate_guidance": "No news found"}
            continue
            
        headlines = [n['title'] for n in news[:5]]
        
        # Filter for guidance/corporate keywords
        guidance_keywords = ["guidance", "management", "ceo", "forecast", "earnings", "outlook"]
        guidance_headlines = [h for h in headlines if any(k in h.lower() for k in guidance_keywords)]
        
        try:
            # Analyze all headlines
            sentiments = sentiment_pipeline(headlines)
            
            # Analyze guidance specifically if exists
            guidance_sentiment_label = "Neutral"
            if guidance_headlines:
                g_sentiments = sentiment_pipeline(guidance_headlines)
                # Pick the most prominent sentiment for guidance
                pos = sum(1 for s in g_sentiments if s['label'] == 'positive')
                neg = sum(1 for s in g_sentiments if s['label'] == 'negative')
                if pos > neg: guidance_sentiment_label = "Positive"
                elif neg > pos: guidance_sentiment_label = "Negative"
                
            # Aggregate overall sentiment
            pos_count = sum(1 for s in sentiments if s['label'] == 'positive')
            neg_count = sum(1 for s in sentiments if s['label'] == 'negative')
            
            overall = "Neutral"
            if pos_count > neg_count: overall = "Positive"
            elif neg_count > pos_count: overall = "Negative"
            
            results[ticker] = {
                "overall": overall,
                "details": [{"headline": h, "sentiment": s['label']} for h, s in zip(headlines, sentiments)],
                "corporate_guidance": guidance_sentiment_label
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}
            
    return {"data": results}

@app.post("/api/ai-predict")
def ai_predict(req: PortfolioRequest, current_user: User = Depends(get_current_user)):
    grok_api_key = os.getenv("GROK_API_KEY")
    if not client and not grok_api_key:
        return {"error": "Neither GEMINI_API_KEY nor GROK_API_KEY is set. Please set one in .env file."}
    
    prompt = f"""
    You are an expert AI quantitative analyst and portfolio manager. 
    The user wants to invest {req.amount} INR.
    Their risk profile is: {req.risk}.
    They are interested in the following sectors: {', '.join(req.sectors) if req.sectors else 'All sectors'}.
    
    Recent Volume Data (Current vs Average): {req.volume_data}
    Current RSI Data: {req.rsi_data}
    
    Please provide:
    1. Market and sector based analysis for the selected sectors.
    2. Any general guidance or outlook from corporates in these sectors (summarized).
    3. Technical & Volume Boundary Analysis: Explain what the RSI metrics (Overbought > 70, Oversold < 30) and volume boundaries (spikes/drop-offs) suggest about the current market phase for the selected stocks/sectors.
    4. Your predictions and recommended allocation strategy based on historical performance, volatility, and technicals.
    
    Return the response strictly as a JSON object with the following keys:
    {{
        "market_analysis": "string detailing the sector analysis",
        "corporate_guidance": "string detailing corporate guidance",
        "technical_analysis": "string detailing the RSI and volume boundary analysis",
        "predictions": "string detailing your predictions and strategy",
        "recommended_allocation": [
             {{"ticker": "RELIANCE.NS", "sector": "Energy", "allocation_pct": 20, "reason": "..."}}
        ]
    }}
    Ensure the sum of allocation_pct equals 100. Provide indian tickers (e.g., .NS suffix) if appropriate or global ones if sectors suggest it. The output MUST be valid JSON.
    """
    try:
        text = ""
        # Primary: Grok
        if grok_api_key:
            try:
                grok_client = OpenAI(
                    api_key=grok_api_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                completion = grok_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "You are a quantitative AI agent. Provide valid JSON only."},
                        {"role": "user", "content": prompt}
                    ]
                )
                text = completion.choices[0].message.content
            except Exception as grok_e:
                print("Grok failed, falling back to Gemini:", grok_e)
                if client:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    text = response.text
                else:
                    raise grok_e
        
        # Primary: Gemini (if Grok not configured)
        elif client:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            text = response.text
        else:
            raise Exception("No AI client configured.")
        
        # Clean response string to parse JSON
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
            
        data = json.loads(text.strip())
        return data
    except Exception as e:
        return {"error": f"AI prediction failed: {str(e)}"}

# Trigger reload
# Reload 2