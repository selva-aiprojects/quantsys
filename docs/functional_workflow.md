# Functional Workflow Document

**Product Name:** QuantSys AI Portfolio Rebalancer (Nivesh)  
**Version:** 1.0  

This document describes the step-by-step functional workflow from the perspective of the user and the system's background processes.

## 1. Onboarding & Landing

### 1.1 Initial Application Load
*   **User Action:** Opens the application URL in a web browser.
*   **System Response:** 
    *   Loads the Single Page Application (SPA).
    *   Checks `localStorage` for any existing saved portfolios.
    *   If saved portfolios exist, defaults the view to the **Saved Portfolios** tab.
    *   If no saved portfolios exist, defaults the view to the **Build your model** tab.

## 2. Portfolio Management (Saved Portfolios Tab)

### 2.1 Viewing Saved Portfolios
*   **User Action:** Navigates to or lands on the **Saved Portfolios** tab.
*   **System Response:** Displays a tabular list of all saved portfolios (Name, Risk Profile, Allocated Amount, Date Last Logged).

### 2.2 Selecting a Portfolio
*   **User Action:** Clicks "Load" on a specific portfolio row.
*   **System Response:** 
    *   Retrieves the stored portfolio parameters (tickers, entry prices, quantities, risk).
    *   Populates the active application state with this data.
    *   Automatically redirects the user to the **Proposed Portfolio** view showing their populated data.

## 3. Portfolio Creation (Build your model Tab)

### 3.1 Defining Parameters
*   **User Action:** Clicks "Create new portfolio with AI" (or navigates to the Build tab).
*   **System Response:** Displays input fields.
*   **User Action:** Enters Total Investment Amount, selects Risk Profile (Conservative, Moderate, Aggressive), and selects Target Sectors.
*   **User Action:** Adjusts Stop-Loss and Rebalance Drift rules if desired.
*   **User Action:** Clicks "Build portfolio".
*   **System Response:** 
    *   Calculates capital allocation based on the risk profile (Large-cap, Mid-cap, Small-cap, Buffer).
    *   Populates the **Proposed Portfolio** table with default representative stocks from the chosen sectors.
    *   Calculates quantities based on user-provided entry prices (defaulting to placeholders).

## 4. Market & AI Analysis (Insights Tab)

### 4.1 Triggering the Analysis
*   **User Action:** From the Proposed Portfolio view, clicks **"✨ AI Predict & Insights"**.
*   **System Response:** 
    *   Displays a loading state.
    *   **Process A (Market Data):** Calls `/api/market-data` to fetch live prices, Trading Volume, Average Volume, and calculates the **Relative Strength Index (RSI)** for each ticker using `yfinance` historical data.
    *   **Process B (FinBERT Sentiment):** Calls `/api/sentiment-analysis`. Fetches recent news via `yfinance`, filters for corporate guidance keywords, and processes text through the local HuggingFace `FinBERT` model.
    *   **Process C (Gemini Predictions):** Calls `/api/ai-predict`. Passes user parameters, fetched RSI, volume boundaries, and market data to the `gemini-2.5-flash` model via a structured prompt.

### 4.2 Reviewing the Results
*   **System Response:** Once all processes complete, updates the UI and reveals the **AI Insights** sub-tabs.
*   **User Action (Sentiment & Market Tab):** Reviews FinBERT sentiment gauges (Positive/Neutral/Negative) for individual tickers and broad sectors, alongside Gemini's macro market analysis.
*   **User Action (Corporate Guidance Tab):** Reviews FinBERT's sentiment scoring specifically isolated to recent corporate/management guidance and earnings news.
*   **User Action (Technical & Prediction Tab):** Reviews the **RSI indicators** (Overbought > 70, Oversold < 30), **Volume Boundary** deviations, and Gemini's tactical recommendations based on these technicals.

## 5. Maintenance & Updating

### 5.1 Updating Entry Prices
*   **User Action:** Edits the "Entry price" field in the Proposed Portfolio table based on real-world brokerage data.
*   **System Response:** Automatically recalculates stock quantities and stop-loss targets dynamically.

### 5.2 Logging a New Snapshot (History)
*   **User Action:** Navigates back to the **Saved Portfolios** tab and clicks "Update loaded portfolio".
*   **System Response:** Appends a new time-stamped snapshot (with the newly edited prices/quantities) to the portfolio's history in `localStorage`. 

### 5.3 Comparing Portfolios
*   **User Action:** Checks the boxes next to two different portfolios in the Saved list and clicks "Compare".
*   **System Response:** Renders a side-by-side comparative breakdown of allocations, sectors, and logged value.
