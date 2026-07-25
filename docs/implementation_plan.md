# Integrate FinBERT, Advanced Analysis, and Streamline Portfolio Selection

This plan covers integrating FinBERT for multi-dimensional sentiment analysis, adding volume-based analytics, and restructuring the application workflow to emphasize Saved Portfolios.

## User Review Required

> [!IMPORTANT]  
> **FinBERT Local Execution**: Installing `transformers` and `torch` for FinBERT will increase the size of the project environment (PyTorch is ~1.5GB). The plan currently assumes **local execution**. Let me know if you prefer a cloud API to save space.

> [!IMPORTANT]  
> **Corporate Guidance Data Source**: `yfinance` provides standard news headlines. To explicitly get "Management/Corporate Guidance", we can prompt the Gemini AI to extract guidance themes, OR filter `yfinance` news for keywords like "guidance", "management", "earnings call" and run FinBERT on those. The plan assumes filtering news and using Gemini to supplement the analysis.

## Proposed Changes

---

### Backend (Python)

#### [MODIFY] [requirements.txt](file:///d:/Training/working/Cognivectra/Nivesh/requirements.txt)
- Add `transformers` and `torch` for local FinBERT model execution.

#### [MODIFY] [main.py](file:///d:/Training/working/Cognivectra/Nivesh/main.py)
- **Model Loading**: Load the `ProsusAI/finbert` pipeline on startup.
- **Enhanced Market Data (`/api/market-data`)**: Update the `yfinance` fetching logic to include **Volume data** (Current Volume, Average Volume) and calculate the **Relative Strength Index (RSI)** based on historical closing prices.
- **New FinBERT Endpoint (`POST /api/sentiment-analysis`)**:
  - Accept tickers and sectors as input.
  - Fetch news for individual tickers AND sector-wide queries.
  - Run FinBERT to categorize sentiment for:
    1. **Ticker-level News**
    2. **Sector-level Sentiment**
    3. **Corporate Guidance**: Filter the news for keywords (e.g., "guidance", "CEO", "management", "forecast") and score the sentiment specifically for these items.
- **Enhanced Gemini Prompt (`/api/ai-predict`)**:
  - Feed the volume data (and calculated volume boundaries/deviations) as well as the **RSI indicators** into the Gemini prompt.
  - Ask Gemini to provide **AI Analysis based on Volume Boundaries and RSI** (e.g., identifying breakouts, accumulation/distribution phases, overbought/oversold conditions).

---

### Frontend (HTML/JS)

#### [MODIFY] [index.html](file:///d:/Training/working/Cognivectra/Nivesh/index.html)
- **Workflow Restructure**: 
  - Make the "Saved Portfolios" tab the default view or highly prominent.
  - Add a clear "Create new portfolio with AI" button that routes to the model builder.
- **Enhanced AI Insights Tab**:
  - Create a new section/tab for **FinBERT Sentiment Analysis**.
  - Display sentiment scores (Positive/Neutral/Negative) split by:
    - Overall Portfolio Sentiment
    - Sector-level Sentiment Analysis
    - Corporate / Management Guidance Sentiment
  - Create a new section/tab for **Technical & Volume Analysis**, displaying the volume boundaries, **RSI indicators**, and the AI's interpretation of these technical trends.

## Verification Plan

### Automated Tests
- No automated tests currently exist; manual verification will be used.

### Manual Verification
- Start the server (`uvicorn main:app --reload`).
- Verify the "Saved Portfolios" UI acts as the primary starting point.
- Trigger the AI flow and ensure `yfinance` volume data is successfully fetched and displayed.
- Click the FinBERT analysis button and verify that Sector Sentiment, Corporate Guidance Sentiment, and Ticker Sentiment are accurately returned and displayed.
