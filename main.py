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
DEFAULT_GOOGLE_CLIENT_ID = "1008485046253-5es0stvufqj5sr31ndkbtsj5v7mv960t.apps.googleusercontent.com"
GOOGLE_CLIENT_ID = (
    os.getenv("GOOGLE_CLIENT_ID", "")
    or os.getenv("google_client_id", "")
    or DEFAULT_GOOGLE_CLIENT_ID
)
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
    sector_weights: dict[str, float] = {}
    stocks: list[dict] = []  # Optional: [{"ticker": "HDFCBANK", "price": 1800, "allocated": 50000}]


class CopilotMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class CopilotRequest(BaseModel):
    message: str
    history: list[CopilotMessage] = []
    portfolio_context: dict = {}  # holdings, metrics etc passed from frontend


class SignalsRequest(BaseModel):
    tickers: list[str]  # NSE tickers without .NS
    portfolio_context: dict = {}


class PortfolioHealthRequest(BaseModel):
    holdings: list[dict]  # [{ticker, qty, avg_cost, current_price, sector, ...}]

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.get("/api/config")
def get_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "") or os.getenv("google_client_id", "") or GOOGLE_CLIENT_ID
    return {"google_client_id": client_id}


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    client_id = os.getenv("GOOGLE_CLIENT_ID", "") or os.getenv("google_client_id", "") or GOOGLE_CLIENT_ID
    return html.replace("__GOOGLE_CLIENT_ID__", client_id)


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
def get_market_data(tickers: str):
    """
    Fetch live market prices directly from Yahoo Finance Chart API (v8/finance/chart).
    Bypasses yfinance to avoid rate-limiting on the quoteSummary endpoint.
    """
    import urllib.request
    import concurrent.futures

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {"error": "No tickers provided"}

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def fetch_price(ticker: str) -> tuple[str, dict]:
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?interval=1d&range=1d&includePrePost=false"
        )
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read())
            meta = raw["chart"]["result"][0]["meta"]
            price = float(
                meta.get("regularMarketPrice")
                or meta.get("chartPreviousClose")
                or 0
            )
            prev_close = float(meta.get("chartPreviousClose") or meta.get("previousClose") or price)
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            return ticker, {
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": meta.get("currency", "INR"),
                "exchange": meta.get("exchangeName", ""),
            }
        except Exception as e:
            # Retry once via query2 host
            try:
                url2 = url.replace("query1.finance.yahoo.com", "query2.finance.yahoo.com")
                req2 = urllib.request.Request(url2, headers=HEADERS)
                with urllib.request.urlopen(req2, timeout=8) as resp2:
                    raw2 = json.loads(resp2.read())
                meta2 = raw2["chart"]["result"][0]["meta"]
                price2 = float(
                    meta2.get("regularMarketPrice")
                    or meta2.get("chartPreviousClose")
                    or 0
                )
                prev_close2 = float(meta2.get("chartPreviousClose") or meta2.get("previousClose") or price2)
                change2 = price2 - prev_close2
                change_pct2 = (change2 / prev_close2 * 100) if prev_close2 else 0.0
                return ticker, {
                    "price": round(price2, 2),
                    "prev_close": round(prev_close2, 2),
                    "change": round(change2, 2),
                    "change_pct": round(change_pct2, 2),
                    "currency": meta2.get("currency", "INR")
                }
            except Exception as e2:
                return ticker, {"price": 0, "error": str(e2)}

    data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(ticker_list), 8)) as pool:
        futures = {pool.submit(fetch_price, t): t for t in ticker_list}
        for future in concurrent.futures.as_completed(futures, timeout=15):
            try:
                ticker, result = future.result()
                data[ticker] = result
            except Exception as exc:
                t = futures[future]
                data[t] = {"price": 0, "error": str(exc)}

    return {"data": data}


@app.get("/api/stock-chart")
def get_stock_chart(ticker: str, period: str = "1y"):
    import yfinance as yf
    try:
        normalized = ticker.strip().upper()
        if not normalized.endswith(".NS"):
            normalized = normalized + ".NS"
        stock = yf.Ticker(normalized)
        interval = "1d"
        if period in ("1mo", "3mo"):
            interval = "1d"
        elif period in ("6mo", "1y"):
            interval = "1d"
        else:
            interval = "1wk"
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            return {"error": "No data available"}
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(float(row["Close"]), 2)
            })
        return {"ticker": normalized, "period": period, "data": data}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/ai-predict")
def ai_predict(req: PortfolioRequest, user: dict = Depends(get_current_user)):
    if not client:
        return {"error": "GEMINI_API_KEY is not set. Please set it in .env file."}

    # Build live price context string
    live_price_context = ""
    stock_tickers = ""
    if req.stocks:
        live_price_context = "Current live market prices: " + ", ".join(
            [f"{s['ticker']} @ ₹{s['price']}" for s in req.stocks if s.get('price', 0) > 0]
        )
        stock_tickers = ", ".join([s["ticker"] for s in req.stocks])
    else:
        stock_tickers = "stocks from sectors: " + ", ".join(req.sectors)

    candidate_tickers = [s["ticker"] for s in req.stocks] if req.stocks else []

    prompt = f"""
You are an expert AI quantitative analyst and portfolio manager for Indian equity markets.
The user wants to invest {req.amount} INR with a {req.risk} risk profile.
Sectors of interest: {', '.join(req.sectors) if req.sectors else 'All sectors'}.
{live_price_context}
Portfolio stocks (NSE tickers): {stock_tickers}
{f'Relative sector weight bias for this risk profile (use as a prior — over/under-weight sectors relative to these values, but keep weights within +/- 10 percentage points of the prior and only among the listed sectors): ' + str(req.sector_weights) if req.sector_weights else ''}

Provide a full analysis covering:
1. Market & sector outlook
2. Corporate guidance from key companies in these sectors
3. Overall predictions & allocation strategy — this MUST include a concrete recommended_allocation
   (see schema below) that reweights the candidate stocks by conviction. Do not default to an
   equal split unless your analysis genuinely supports equal weighting; favour stocks with
   stronger relative momentum, valuation, or guidance and underweight/exclude weaker ones.
4. SELL SIGNALS — stocks that are overvalued, technically weak, or facing headwinds
5. SHORT-TERM (1–4 weeks) momentum-based BUY/SELL/HOLD for each portfolio stock
6. LONG-TERM (6–18 months) fundamental conviction ratings for each portfolio stock

Constraints for "recommended_allocation" specifically:
- Only use tickers from this exact candidate list (no others, no invented tickers): {candidate_tickers if candidate_tickers else 'use well-known NSE large-cap tickers for the given sectors'}.
- You may assign 0% (i.e. omit) a candidate you have no conviction in, but do not invent tickers
  outside the candidate list.
- allocation_pct values across the array must sum to exactly 100.
- This allocation represents ONLY the large-cap stock-picking sleeve of the portfolio (not the
  mid-cap/small-cap ETF sleeves or cash buffer), so weight purely by relative conviction among
  the candidates.
- target_price in every signal array must be a real numeric estimate derived from the live price
  given above (price * expected move), never the literal value null — omit the key entirely for
  a stock only if truly no live price was supplied for it.

Return ONLY a valid JSON object with these exact keys (no markdown, no extra text):
{{
    "market_analysis": "detailed sector & macro analysis string",
    "corporate_guidance": "string summarising corporate earnings guidance & outlooks",
    "predictions": "string with overall strategy & allocation thesis",
    "recommended_allocation": [
        {{"ticker": "TICKER.NS", "sector": "SectorName", "allocation_pct": 20, "reason": "brief reason"}}
    ],
    "sell_signals": [
        {{"ticker": "TICKER", "action": "SELL", "reason": "concise reason", "target_price": 1234.5}}
    ],
    "sell_analysis": "string — overall narrative for why sell signals were generated now",
    "short_term_signals": [
        {{"ticker": "TICKER", "action": "BUY|SELL|HOLD", "reason": "momentum/news rationale", "target_price": 1234.5}}
    ],
    "short_term_analysis": "string — short-term market environment overview",
    "long_term_signals": [
        {{"ticker": "TICKER", "action": "STRONG BUY|BUY|HOLD|ACCUMULATE ON DIPS|SELL", "reason": "fundamental thesis", "target_price": 1234.5}}
    ],
    "long_term_analysis": "string — long-term fundamental thesis for the portfolio"
}}

Rules:
- Use exact NSE ticker symbols (e.g. HDFCBANK, TCS, INFY) in signal arrays — no .NS suffix.
- recommended_allocation allocation_pct values must sum to 100.
- If live prices were provided, factor them into your target_price estimates.
- target_price must always be a number, never null/None — compute it from the live price and your
  directional view; the 1234.5 above is just a placeholder to show the field is numeric.
- Every signal array must have one entry per portfolio stock at minimum.
- Output MUST be valid JSON only.
"""

    try:
        text = _call_gemini(prompt)
        return json.loads(text)
    except Exception as e:
        err_str = str(e)
        if any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded"]):
            return {"error": "AI API rate limit reached. Please wait 30 seconds and try again."}
        return {"error": f"AI prediction failed: {err_str}"}


# ──────────────────────────────────────────────────────────────
# SmartPortfolio V2 — New Endpoints
# ──────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    """Helper: call Gemini with fallback between models, then Grok (xAI)."""
    if not client:
        raise ValueError("GEMINI_API_KEY not set")
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest"]:
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            text = resp.text.strip()
            for fence in ("```json", "```"):
                if text.startswith(fence):
                    text = text[len(fence):]
            if text.endswith("```"):
                text = text[:-3]
            return text.strip()
        except Exception as e:
            err = str(e)
            if any(k in err for k in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                continue
            raise
    # Fallback to Grok (xAI)
    try:
        return _call_grok(prompt)
    except Exception as e:
        raise RuntimeError(f"All LLM providers failed: {e}")


def _call_grok(prompt: str) -> str:
    """Fallback: call xAI Grok API."""
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        raise ValueError("GROK_API_KEY not set")

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    def _request(model: str) -> str:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            text = data["choices"][0]["message"]["content"].strip()
            for fence in ("```json", "```"):
                if text.startswith(fence):
                    text = text[len(fence):]
            if text.endswith("```"):
                text = text[:-3]
            return text.strip()

    try:
        return _request("grok-3-beta")
    except Exception:
        return _request("grok-2-latest")


@app.post("/api/ai-copilot")
def ai_copilot(req: CopilotRequest, user: dict = Depends(get_current_user)):
    """Portfolio-aware AI Copilot chat endpoint."""
    if not client:
        return {"error": "GEMINI_API_KEY not set"}

    ctx = req.portfolio_context
    holdings_text = ""
    if ctx.get("holdings"):
        lines = []
        for h in ctx["holdings"]:
            pnl_pct = ((h.get("current_price", 0) - h.get("avg_cost", 0)) / h.get("avg_cost", 1)) * 100
            lines.append(
                f"  - {h.get('ticker')}: {h.get('qty')} shares @ ₹{h.get('avg_cost')}, "
                f"LTP ₹{h.get('current_price', 'N/A')}, P&L {pnl_pct:.1f}%, "
                f"Sector: {h.get('sector', 'N/A')}, Allocation: {h.get('allocation_pct', 0):.1f}%"
            )
        holdings_text = "\n".join(lines)

    system_prompt = f"""You are SmartPortfolio AI Copilot — a professional, data-driven portfolio intelligence assistant for Indian equity markets.

PORTFOLIO CONTEXT:
Total Value: ₹{ctx.get('total_value', 'N/A')}
Invested: ₹{ctx.get('invested', 'N/A')}
Today's P&L: ₹{ctx.get('today_pnl', 'N/A')} ({ctx.get('today_pnl_pct', 'N/A')}%)
Total P&L: ₹{ctx.get('total_pnl', 'N/A')} ({ctx.get('total_pnl_pct', 'N/A')}%)
Portfolio Health: {ctx.get('health_score', 'N/A')}/100
Holdings:
{holdings_text or '  No holdings provided.'}

INSTRUCTIONS:
- Answer ONLY based on the portfolio context and your market knowledge.
- Be concise, analytical, and professional — like a portfolio manager.
- Use specific numbers and percentages from the portfolio context.
- For any recommendation, use: ACCUMULATE / HOLD / WATCH / REDUCE / EXIT CANDIDATE signals only.
- Always add: "This is analytical information, not investment advice. Data as of [today's date]."
- Never guarantee returns or use "buy/sell" as absolute commands.
- Format with clear structure. Keep responses under 300 words unless asked for detail.

CONVERSATION HISTORY:
{chr(10).join([f'{m.role.upper()}: {m.content}' for m in req.history[-6:]])}

USER: {req.message}
ASSISTANT:"""

    try:
        text = _call_gemini(system_prompt)
        return {"response": text}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/ai-signals")
def ai_signals(req: SignalsRequest, user: dict = Depends(get_current_user)):
    """Generate AI signals for a batch of holdings."""
    if not client:
        return {"error": "GEMINI_API_KEY not set"}
    if not req.tickers:
        return {"signals": []}

    ctx = req.portfolio_context
    tickers_str = ", ".join(req.tickers)

    prompt = f"""You are a quantitative analyst for Indian equity markets. Analyze these NSE stocks and return structured signals.

Portfolio Context:
Total Value: ₹{ctx.get('total_value', 'N/A')}
Holdings: {tickers_str}

For each stock in the list, provide a signal based on current market conditions, fundamentals, and valuation as of August 2026.

Return ONLY valid JSON array (no markdown, no extra text):
[
  {{
    "ticker": "HDFCBANK",
    "signal": "HOLD",
    "confidence": 78,
    "quant_score": 72,
    "fundamental_score": 84,
    "technical_score": 76,
    "valuation_score": 69,
    "momentum_score": 73,
    "reasoning": "Brief 1-2 sentence reasoning",
    "key_risk": "Main risk factor",
    "3m_range_low": 1550,
    "3m_range_high": 1700,
    "3m_probability": 55
  }}
]

Signal must be one of: ACCUMULATE, HOLD, WATCH, REDUCE, EXIT CANDIDATE
confidence: 0-100
All scores: 0-100
All stocks in [{tickers_str}] must appear in the response."""

    try:
        text = _call_gemini(prompt)
        signals = json.loads(text)
        return {"signals": signals}
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response", "raw": text[:500]}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/stock-summary")
def stock_summary(ticker: str):
    """Fetch stock fundamentals summary from yfinance."""
    import yfinance as yf
    try:
        normalized = ticker.strip().upper()
        if not normalized.endswith(".NS"):
            normalized += ".NS"
        stock = yf.Ticker(normalized)
        info = stock.info
        return {
            "ticker": normalized,
            "name": info.get("longName") or info.get("shortName", normalized),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "debt_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "avg_volume": info.get("averageVolume"),
            "description": (info.get("longBusinessSummary") or "")[:400],
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "eps": info.get("trailingEps"),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@app.post("/api/portfolio-health")
def portfolio_health(req: PortfolioHealthRequest):
    """Compute portfolio health score from holdings."""
    holdings = req.holdings
    if not holdings:
        return {"score": 0, "breakdown": {}}

    num = len(holdings)
    total_val = sum(h.get("current_price", 0) * h.get("qty", 0) for h in holdings)
    if total_val == 0:
        return {"score": 0, "breakdown": {}}

    # Concentration score (lower top-5 concentration = better)
    allocations = sorted(
        [(h.get("current_price", 0) * h.get("qty", 0)) / total_val for h in holdings],
        reverse=True
    )
    top5 = sum(allocations[:5])
    concentration_score = max(0, 100 - int(top5 * 100))  # 0% concentration = 100 score

    # Diversification score (more unique sectors = better)
    sectors = set(h.get("sector", "Unknown") for h in holdings)
    diversification_score = min(100, len(sectors) * 14)

    # Liquidity (approximate: number of holdings > 5 = good)
    liquidity_score = min(100, num * 8 + 20)

    # Simple P&L quality score
    gainers = sum(1 for h in holdings if (h.get("current_price", 0) - h.get("avg_cost", 0)) > 0)
    quality_score = int((gainers / num) * 100) if num else 50

    # Composite
    overall = int(
        concentration_score * 0.20 +
        diversification_score * 0.25 +
        liquidity_score * 0.15 +
        quality_score * 0.40
    )

    return {
        "score": min(100, overall),
        "breakdown": {
            "diversification": min(100, diversification_score),
            "concentration": min(100, concentration_score),
            "liquidity": min(100, liquidity_score),
            "quality": min(100, quality_score),
            "risk": max(0, 100 - concentration_score),
            "momentum": quality_score,
        },
        "top5_concentration_pct": round(top5 * 100, 1),
        "sector_count": len(sectors),
        "holdings_count": num,
    }