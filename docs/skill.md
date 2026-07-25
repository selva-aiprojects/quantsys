---
name: Nivesh Quantitative Analysis Protocol
description: Guidelines and instructions for analyzing portfolios, processing FinBERT sentiments, and evaluating technical indicators (RSI, Volume) in the Nivesh system.
---

# Nivesh Quantitative Analysis Protocol

When working on the Nivesh QuantSys codebase (or generating insights/documentation for it), you must adhere to the following architecture and logic rules:

## 1. Dual-Model Architecture
Nivesh relies on two AI models that serve distinct purposes:
- **FinBERT (ProsusAI/finbert)**: Used strictly for **Sentiment Analysis**. FinBERT processes recent news headlines fetched via yfinance to output explicit Positive/Negative/Neutral classifications. It is particularly used to isolate **Corporate Guidance** (by filtering for keywords like "guidance", "ceo", "forecast") and evaluate **Overall Ticker Sentiment**.
- **Gemini (gemini-2.5-flash)**: Used for **Macro, Tactical, and Technical reasoning**. Gemini takes structured inputs (Risk Profile, Investment Amount, Sectors, RSI bounds, and Volume data) and generates human-readable strategy, predictions, and allocation percentages.

## 2. Technical Indicators (RSI & Volume Boundaries)
- **RSI (Relative Strength Index)**: We strictly calculate 14-day RSI based on daily closing prices. Overbought bounds are considered > 70 and Oversold bounds < 30.
- **Volume Boundaries**: We compare Current Volume against a 30-day Average Volume. Spikes in volume, when passed to Gemini alongside RSI, are used to evaluate accumulation vs. distribution phases.

## 3. Workflow Priorities
- The primary user entry point is the **Saved Portfolios** view. All workflows should assume users are iterating upon saved, tracked portfolios before they decide to construct entirely new ones.
- When generating UI components, use the established custom CSS variables (e.g., --teal, --amber, --bg-deep) and maintain the dark-mode aesthetic with monospace fonts (IBM Plex Mono) for financial figures.

## 4. Maintenance
- Any new technical indicators added in the future must be fetched/calculated in the /api/market-data endpoint in main.py and passed down to the frontend, which will subsequently route them to the /api/ai-predict endpoint if AI interpretation is needed.
