# Product Requirements Document (PRD)

**Product Name:** QuantSys AI Portfolio Rebalancer (Nivesh)  
**Document Version:** 1.0  
**Date:** July 2026  

## 1. Executive Summary
QuantSys is an AI-driven, self-refinement portal for Indian equity market allocation and risk-rule modeling. The upcoming release aims to significantly enhance the user experience by prioritizing the management of "Saved Portfolios" while introducing deep quantitative and qualitative AI analysis using **Google Gemini** and **FinBERT**. The enhancements will allow investors to analyze market sentiment at a granular level (ticker, sector, corporate guidance) and leverage volume-boundary analysis for better market timing and risk assessment.

## 2. Target Audience
- Retail investors in the Indian Equity Market (NSE/BSE).
- Quantitative enthusiasts and users looking for structured, rule-based investing frameworks.
- Users seeking AI-driven insights on portfolio allocation, sector trends, and sentiment.

## 3. Technology Stack

### Backend
*   **Language:** Python 3.x
*   **Framework:** FastAPI (REST API, static file serving)
*   **Server/ASGI:** Uvicorn
*   **Financial Data:** `yfinance` (Real-time pricing, historical data, volume, and news fetching)
*   **Generative AI:** Google GenAI SDK (`gemini-2.5-flash`) for predictive modeling, allocation, and text-based analytics.
*   **NLP/Sentiment Analysis:** Hugging Face `transformers` & `torch` using the `ProsusAI/finbert` model (or equivalent financial sentiment model).
*   **Environment Management:** `python-dotenv`

### Frontend
*   **Core:** HTML5, CSS3 (Vanilla, custom CSS variables for theming), Vanilla JavaScript.
*   **Architecture:** Single Page Application (SPA) feel with dynamic DOM manipulation.
*   **Storage:** `localStorage` for saving portfolio snapshots and historical tracking.
*   **Typography:** Google Fonts (Space Grotesk, Inter, IBM Plex Mono).

---

## 4. Feature Requirements

### 4.1. Streamlined Portfolio Workflow
**Goal:** Make the "Saved Portfolios" feature the primary entry point for returning users, while keeping the AI portfolio builder easily accessible.

*   **REQ-4.1.1 (Default Landing):** The application UI must emphasize the "Saved Portfolios" view. If a user has saved portfolios, this tab should be immediately visible or act as the default landing tab upon visiting the application.
*   **REQ-4.1.2 (Portfolio Selection):** Users must be able to select a saved portfolio from a list. Selecting a portfolio will load its saved state (amount, risk, sectors, tickers, entry prices).
*   **REQ-4.1.3 (AI Creation Entry Point):** A clear, distinct call-to-action (e.g., "Create new portfolio with AI") must be available to route users to the "Build your model" tab.
*   **REQ-4.1.4 (Historical Tracking):** The existing capability to log historical values and track percentage changes over time for saved portfolios must be maintained.

### 4.2. Advanced Sentiment Analysis (FinBERT Integration)
**Goal:** Provide actionable sentiment analysis on market news, sector trends, and corporate guidance using FinBERT.

*   **REQ-4.2.1 (Ticker Sentiment):** The backend must expose an API endpoint (`/api/sentiment-analysis`) that accepts a list of stock tickers. It must fetch recent news headlines for these tickers via `yfinance` and score the sentiment (Positive, Negative, Neutral) using FinBERT.
*   **REQ-4.2.2 (Sector Sentiment):** The application must be able to evaluate the aggregate sentiment of a selected sector (e.g., IT, Banking) by analyzing news related to the top constituents of that sector.
*   **REQ-4.2.3 (Corporate Guidance Sentiment):** The backend must filter news items/transcripts for keywords related to corporate or management guidance (e.g., "guidance", "management", "CEO", "forecast", "earnings"). It will apply FinBERT specifically to these filtered items to provide a distinct "Corporate Guidance Sentiment" score.
*   **REQ-4.2.4 (UI Integration):** The AI Insights tab must be updated to display visual sentiment indicators (e.g., gauges, tags, or progress bars) reflecting the FinBERT scores for the portfolio, individual sectors, and corporate guidance.

### 4.3. AI Analysis Based on Volume Boundaries
**Goal:** Enhance the Gemini AI prediction model by incorporating trading volume analytics to identify accumulation/distribution phases or breakout potential.

*   **REQ-4.3.1 (Technical Data Fetching):** The `/api/market-data` endpoint (or a new dedicated endpoint) must fetch both Current Trading Volume, Average Trading Volume (e.g., 10-day or 30-day average), and calculate the **Relative Strength Index (RSI)** (typically a 14-day period) for the selected tickers.
*   **REQ-4.3.2 (Technical Boundary Calculation):** The backend must calculate volume deviations (e.g., volume spikes > 150% of the average volume) and RSI bounds (Overbought > 70, Oversold < 30).
*   **REQ-4.3.3 (Prompt Engineering):** The prompt sent to `gemini-2.5-flash` in `/api/ai-predict` must be updated to include this volume and RSI data.
*   **REQ-4.3.4 (AI Output):** The Gemini model must explicitly output a section titled "Technical & Volume Boundary Analysis", explaining what the RSI metrics and volume suggest about the current market phase for the selected stocks/sectors.
*   **REQ-4.3.5 (UI Integration):** The AI Insights tab must include a dedicated view or panel to display the AI's interpretation of the volume boundaries and RSI indicators.

---

## 5. User Experience (UX) Flow

1.  **User Accesses App:**
    *   *If New User:* Lands on "Build your model". Enters investment amount, selects risk profile and sectors. Builds portfolio.
    *   *If Returning User:* Lands on "Saved Portfolios". Sees a list of their previously saved portfolios.
2.  **Portfolio Interaction:**
    *   The user selects a saved portfolio. The app populates the stock list, allocations, and saved entry prices.
3.  **AI & Market Insights:**
    *   The user clicks **"✨ AI Predict & Insights"**.
    *   The app fetches live prices and volume data.
    *   The app fetches news and runs FinBERT sentiment analysis.
    *   The app queries Gemini with the risk profile, sectors, and volume data.
4.  **Reviewing Insights:**
    *   The user navigates the AI tabs to review:
        *   Market & Sector Analysis (Gemini + FinBERT Sector Sentiment)
        *   Corporate Guidance (Gemini + FinBERT Guidance Sentiment)
        *   Volume Boundary Analysis (Gemini)
        *   AI Predictions & Strategy (Gemini)

## 6. Non-Functional Requirements

*   **Performance:** Given that running FinBERT locally can be resource-intensive, the sentiment analysis endpoint must execute asynchronously where possible to prevent blocking the FastAPI server.
*   **Error Handling:** If `yfinance` fails to fetch news or volume data (which can happen due to API rate limits or missing data for Indian tickers), the UI must fail gracefully, displaying a fallback message rather than breaking the application.
*   **Environment Size:** The deployment environment must account for the increased size requirement (approx 1.5GB to 2GB) due to PyTorch and Transformers dependencies.

## 7. Future Considerations (Out of Scope for this Release)
*   User authentication and cloud database storage (currently relies on `localStorage`).
*   Direct broker integration for live trading.
*   Intraday data analysis (currently focusing on daily/historical metrics).
