from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="QuantSys AI Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        return f.read()

@app.get("/api/market-data")
def get_market_data(tickers: str):
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
def ai_predict(req: PortfolioRequest):
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
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # Clean response string to parse JSON
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
            
        data = json.loads(text.strip())
        return data
    except Exception as e:
        return {"error": f"AI prediction failed: {str(e)}"}
