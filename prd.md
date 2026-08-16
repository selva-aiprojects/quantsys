SmartPortfolio V2 — Product Requirements Document

Product: SmartPortfolio
Current Product: QuantAnalysis / SmartPortfolio
Current URL: QuantAnalysis / SmartPortfolio
Version: V2.0
Date: August 2026
Product Type: AI-powered Portfolio Intelligence & Investment Analytics Platform
Primary Market: India initially; architecture should support global markets later

1. Product Vision
Current positioning

The existing application is essentially:

AI-assisted portfolio analysis and stock prediction

The V2 product should become:

An intelligent portfolio operating system that helps investors understand, monitor, analyze, simulate and improve their actual investment portfolio.

Core proposition

Track → Understand → Analyze → Simulate → Decide → Monitor

The product should not feel like an AI chatbot attached to a stock dashboard.

It should feel like a professional investment terminal with an AI intelligence layer.

2. Product Goals
Primary goals
Accurately track actual portfolios.
Provide institutional-style portfolio analytics in a simple UI.
Explain why portfolio performance changes.
Identify portfolio risks and opportunities.
Provide AI-assisted stock/position analysis.
Calculate correct average acquisition price.
Provide "what-if" investment simulations.
Provide transparent AI confidence and reasoning.
Track AI prediction accuracy over time.
Eventually connect to brokers for portfolio synchronization and execution.
Non-goals for V2

Do not initially attempt to become:

Zerodha replacement
Full brokerage
Autonomous trading bot
Guaranteed-return platform
Fully automated investment adviser

The regulatory distinction matters. SEBI defines investment advice broadly around recommendations relating to investing, purchasing or selling securities, and its current regulations place responsibility on advisers using AI for the security, integrity and outputs of AI systems.

Therefore V2 should initially emphasize portfolio intelligence / analytics / decision support, with appropriate disclosures.

3. Target Users
Persona 1 — Serious Retail Investor

Owns 10–50 stocks.

Needs:

P&L
Average price
Portfolio health
Risk
AI insights
Buy-more simulations
Exit/review signals

Primary target.

Persona 2 — Active Investor

Owns multiple portfolios.

Needs:

Technical analysis
Momentum
Signals
Alerts
Benchmarking
Transaction history
Broker synchronization
Persona 3 — Long-term Investor

Needs:

CAGR
XIRR
Wealth growth
Allocation
Fundamental quality
Risk
Rebalancing
Persona 4 — Financial Professional

Future phase.

Needs:

Multiple clients
Portfolio reports
Model portfolios
Research
Alerts
Audit trail

This persona should not drive V2 architecture initially.

4. New Product Architecture

The product should be organized into six major domains.

SMARTPORTFOLIO
│
├── DASHBOARD
│
├── PORTFOLIO
│   ├── Holdings
│   ├── Transactions
│   ├── P&L
│   ├── Dividends
│   └── Portfolio Health
│
├── INTELLIGENCE
│   ├── AI Copilot
│   ├── AI Signals
│   ├── Portfolio Review
│   └── Risk Radar
│
├── RESEARCH
│   ├── Stocks
│   ├── Screener
│   ├── Watchlist
│   ├── Market
│   └── News
│
├── ANALYTICS
│   ├── Stock Analysis
│   ├── Simulator
│   ├── What-if Analysis
│   ├── Benchmark
│   └── Performance
│
└── TRADING
    ├── Broker Accounts
    ├── Positions
    ├── Orders
    └── Trade History
5. Major Revamp Areas

This is the most important part of the PRD.

Revamp Area 1 — Dashboard
Current problem

The existing dashboard is more analytical/configuration-oriented.

V2

Dashboard becomes the Portfolio Command Center.

Layout
┌──────────────────────────────────────────────┐
│ Portfolio Value            Today's P&L       │
│ ₹24.82L                    +₹18,430 +0.75%   │
├──────────────────────────────────────────────┤
│ Portfolio Health       81 / 100              │
│ ████████████████░░                           │
├──────────────────────┬───────────────────────┤
│ Allocation            │ Performance           │
│ Sector/Asset          │ Portfolio vs Index    │
├──────────────────────┼───────────────────────┤
│ AI Portfolio Brief                          │
│                                             │
│ 3 things require your attention             │
├──────────────────────┼───────────────────────┤
│ Opportunities         │ Risks                 │
│ 2 stocks              │ 3 alerts              │
└──────────────────────┴───────────────────────┘
6. Dashboard Requirements
KPI cards
Total Portfolio Value
Invested Capital
Today's P&L
Total P&L
Total P&L %
XIRR
Cash
Portfolio Health
Secondary metrics
NIFTY comparison
Alpha
Beta
Volatility
Max Drawdown
Sharpe Ratio
Sortino Ratio
AI summary

Example:

Portfolio Brief

Your portfolio gained 0.75% today, outperforming NIFTY 50 by 0.33%.

Technology exposure has increased to 31.8%.

HDFCBANK entered the preferred accumulation zone.

INFY momentum has weakened.

7. Revamp Area 2 — Portfolio

This becomes the core system of record.

Holdings table
Stock	Qty	Avg Cost	LTP	Invested	Value	P&L	P&L %	AI
HDFCBANK	100	₹1,480	₹1,620	₹1.48L	₹1.62L	₹14K	9.46%	HOLD
TCS	50	₹3,220	₹3,080	₹1.61L	₹1.54L	-₹7K	-4.35%	WATCH
Filters
Profit / Loss
Sector
Market Cap
AI Signal
Allocation
Risk
Performance
Watchlist
Actions
View
Analyze
Simulate
Add transaction
Add alert
8. Revamp Area 3 — Transaction Engine

This is essential.

Instead of simply storing:

Stock
Quantity
Average Price

create a transaction ledger.

Transaction types
BUY
SELL
DIVIDEND
BONUS
SPLIT
RIGHTS
MERGER
DEMERGER
BUYBACK
Required calculations
Total invested
Current value
Realized P&L
Unrealized P&L
Average acquisition cost
Quantity
Holding period
XIRR
9. Average Price Engine

This should be deterministic.

Example:

Existing:

100 shares
Average cost = ₹1,400

New purchase:

50 shares
Price = ₹1,200

New average:

(100 × 1400 + 50 × 1200)
--------------------------------
150


= ₹1,333.33
AI should NOT calculate this.

AI can instead recommend:

"Adding at ₹1,200 would reduce your average cost to ₹1,333, but would increase your portfolio exposure from 7.2% to 10.1%."

10. Revamp Area 4 — Stock Intelligence

This should become one of the strongest V2 screens.

Stock header
HDFCBANK


₹1,620.30


+1.42%


Market Cap
P/E
52W High
52W Low
AI Decision
HOLD

Confidence: 78%

Decision factors
Factor	Score
Fundamentals	84
Technical	76
Valuation	69
Momentum	73
Quality	86
Risk	72
11. AI Investment Thesis

The screen should explain:

Why this stock?
What's improving?
What's deteriorating?
Key risks
What would change the AI decision?

Example:

Revenue growth remains healthy and profitability is stable. However, valuation is above the historical median.

Decision: HOLD.

The model would become more positive if earnings revisions improve or valuation falls into the accumulation zone.

This is much better than:

"AI says BUY."

12. AI Decision Framework

Standardize decisions.

Signals

🟢 ACCUMULATE

🟢 HOLD

🟡 WATCH

🟠 REDUCE

🔴 EXIT CANDIDATE

Never use

❌ Guaranteed Buy
❌ Guaranteed Sell
❌ Guaranteed Return

SEBI specifically warns investors about assured-return claims and unregistered investment-advisory activity.

13. Revamp Area 5 — Quant Score Engine

This is where the product becomes technically differentiated.

Proposed score
Fundamental       25%
Technical         20%
Valuation         15%
Momentum          10%
Quality           10%
Risk              10%
Sentiment          5%
Portfolio Fit      5%
----------------------
Total             100%
Output
0–39     Exit Candidate
40–49    Reduce
50–59    Watch
60–69    Hold
70–79    Positive
80–100   Strong Conviction

The actual weights should be configurable.

14. AI Layer

The AI should explain structured quantitative output.

Not independently manufacture investment signals.

Architecture:

Market Data
     ↓
Data Normalization
     ↓
Quant Engines
     ↓
Scores
     ↓
Decision Engine
     ↓
LLM Reasoning
     ↓
User Explanation

This also gives you much better auditability.

15. Revamp Area 6 — AI Portfolio Copilot

This becomes the central AI feature.

Suggested questions

Why is my portfolio down today?

Which stocks are hurting my portfolio?

Which holdings have deteriorated?

Which stocks are overvalued?

Where am I over-concentrated?

What happens if I invest ₹2 lakh?

Which stocks are in accumulation zones?

What are my biggest portfolio risks?

Compare my portfolio with NIFTY 50.

Show stocks where fundamentals improved but price hasn't reacted.

16. Portfolio-Aware AI

The AI must have controlled access to:

Portfolio
Transactions
Holdings
Market data
Fundamentals
Technical indicators
News
Risk metrics
Historical predictions

Example:

User:

"Should I buy more TCS?"

AI:

Your current TCS allocation is 11.8%, above your target 10%.

TCS fundamentals remain strong, but current valuation is neutral and momentum has weakened.

Portfolio decision: HOLD

If you want to increase exposure, consider waiting for the accumulation zone rather than increasing the position at the current allocation.

That is far more useful than a generic stock answer.

17. Revamp Area 7 — Portfolio Simulator

This should be a major feature.

Scenario

What if I invest ₹2,00,000?

User selects:

Existing holding
New stock
Multiple stocks
Percentage allocation
Output
Current Portfolio
₹24.8L


New Investment
₹2L


Projected Portfolio
₹26.8L

Then:

Allocation change

Before → After

Risk change

Before → After

Expected return range
Concentration change
AI assessment

This allocation improves diversification but increases financial-sector exposure by 4.2%.

18. Stock-Level Simulator

For each stock:

"What if I buy more?"

Input:

Current Quantity
100


Average Cost
₹1,480


Current Price
₹1,620


Additional Investment
₹50,000

Output:

New Quantity
130.86


New Average
₹1,533


New Allocation
9.4%


New Portfolio Risk
Moderate
19. Revamp Area 8 — Portfolio Health

Create a single score.

Portfolio Health: 81/100

Breakdown:

Diversification       82
Risk                   76
Quality                86
Valuation              73
Momentum               79
Concentration          68
Liquidity              91
AI interpretation

Portfolio quality is strong, but concentration risk is elevated due to technology exposure.

20. Revamp Area 9 — Risk Radar

Dedicated screen.

Risk categories
Concentration
Sector
Market Cap
Volatility
Correlation
Drawdown
Liquidity
Valuation
Event Risk
Example
PORTFOLIO RISK


Moderate
63 / 100


⚠ Technology concentration
⚠ Top 5 holdings = 57%
⚠ High correlation between 3 positions


✓ Good liquidity
✓ Diversified across 7 sectors
21. Revamp Area 10 — Performance Analytics

Create professional performance analytics.

Charts
Portfolio value
Invested capital
P&L
Daily return
Monthly return
Annual return
Metrics
Absolute return
CAGR
XIRR
Alpha
Beta
Sharpe
Sortino
Volatility
Maximum drawdown
Benchmark
Portfolio       +14.2%
NIFTY 50         +11.8%
NIFTY 500        +12.6%


Alpha            +2.4%
22. Revamp Area 11 — AI Signals

Dedicated signal center.

AI SIGNALS


12 Holdings


🟢 ACCUMULATE
2


🟢 HOLD
6


🟡 WATCH
3


🟠 REDUCE
1

Clicking each signal opens the reasoning.

23. AI Prediction System

Instead of one target price:

Forecast

3 Months

₹1,550–₹1,700

Confidence: 71%

Scenario model
Scenario	Probability	Range
Bear	20%	₹1,300–₹1,450
Base	55%	₹1,550–₹1,700
Bull	25%	₹1,750–₹1,900

This is considerably more useful than a single AI target price.

24. AI Prediction Track Record

This could become a signature feature.

Every prediction gets stored.

Prediction
──────────────
Stock: HDFCBANK
Date: 16-Aug-26


Expected:
₹1,550–₹1,700


Confidence:
71%

Later:

Actual:
₹1,632


Result:
✓ Within prediction range

Dashboard:

AI Track Record
3M Direction Accuracy       74%
3M Range Accuracy           69%
6M Direction Accuracy       67%
Accumulation Signals        76%
Reduce Signals              71%

This creates transparency and prevents the AI from becoming marketing hype.

25. Revamp Area 12 — Watchlist

Watchlist should become intelligent.

Instead of:

RELIANCE
TCS
INFY

show:

Stock	Price	Score	Valuation	AI
RELIANCE	₹1,410	82	Fair	HOLD
INFY	₹1,520	74	Attractive	ACCUMULATE
TCS	₹3,080	61	Expensive	WATCH
26. Revamp Area 13 — Smart Screener

Filters:

Fundamental
Revenue growth
Profit growth
ROE
ROCE
Debt/Equity
Operating margin
Technical
RSI
MACD
Moving average
Momentum
Breakout
Valuation
P/E
P/B
EV/EBITDA
Historical valuation
AI
AI score
Confidence
Accumulation zone
Risk
Portfolio fit
27. Revamp Area 14 — Alerts
Price alerts

HDFCBANK below ₹1,550

AI alerts

AI score dropped below 60

Portfolio alerts

Technology allocation exceeded 30%

Risk alerts

Portfolio drawdown exceeded 8%

Fundamental alerts

EPS estimate revised downward

Corporate alerts

Dividend announced

28. Revamp Area 15 — Broker Integration

Not mandatory for V2.0.

Design the architecture now.

Phase 1

CSV import.

Phase 2

Broker connectivity.

Zerodha
Upstox
Angel One
Dhan
Fyers
Groww
ICICI Direct
Phase 3

Orders.

SmartPortfolio
      ↓
Broker API
      ↓
Order
      ↓
Execution
      ↓
Confirmation
      ↓
Portfolio reconciliation

Execution should always require explicit user confirmation in the initial implementation.

29. Data Architecture

I recommend separating the system into these layers.

                    FRONTEND
                       │
                Next.js / React
                       │
                       ▼
                 API / Backend
                       │
        ┌──────────────┼──────────────┐
        │              │              │
 Portfolio        Market Data      AI Layer
 Engine           Engine           Engine
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Quant Engine
                       │
                 PostgreSQL
                       │
              Historical Data
30. Core Database Entities

Minimum V2 model:

users
portfolios
portfolio_accounts
holdings
transactions
orders
cash_transactions


instruments
instrument_prices
instrument_fundamentals
corporate_actions


sectors
indices
market_data


watchlists
watchlist_items


portfolio_snapshots
portfolio_metrics


risk_scores
quant_scores
ai_signals
ai_predictions
ai_prediction_results


alerts
alert_rules


ai_conversations
ai_messages


benchmarks
31. Critical Database Principle

Separate:

Raw facts

from:

Calculated metrics

from:

AI interpretation

Example:

Transaction
     ↓
Holding
     ↓
P&L calculation
     ↓
Quant score
     ↓
AI explanation

Never store AI output as the source of truth for financial calculations.

32. AI Architecture

Use an agent/tool architecture rather than one huge prompt.

Portfolio Agent
       │
       ├── Portfolio Tool
       ├── Market Tool
       ├── Fundamentals Tool
       ├── Technical Tool
       ├── Risk Tool
       ├── News Tool
       └── Simulation Tool

The LLM becomes the orchestration/reasoning layer.

Given your existing experience with LangGraph/LangChain/CrewAI, this is a good fit.

33. AI Guardrails

Every AI response should have:

Source

Where the data came from.

Timestamp

When the data was retrieved.

Confidence

How confident the model is.

Reasoning

Why the signal exists.

Limitations

What could invalidate it.

Example:

HOLD — 78% confidence

Based on fundamentals, technical indicators, valuation and current portfolio allocation.

Data updated: 16 Aug 2026, 12:20 PM IST.

This is analytical information, not a guaranteed outcome.

If the product later moves into regulated advisory/research services, AI use, disclosures, suitability, records and auditability will need to be designed with the applicable SEBI framework. SEBI's materials specifically address AI use in investment-advisory and research services.

34. UI/UX Redesign

I would move away from the current "AI dashboard" visual style.

Target visual language

Professional fintech terminal

Not:

❌ ChatGPT-like

❌ Gaming dashboard

❌ Excessive gradients

❌ Too many cards

Instead:

Design principles
Dark/light theme
High information density
Clean typography
Compact tables
Professional charts
Consistent green/red semantics
Minimal animation
Strong hierarchy
Desktop-first
Responsive mobile

Think:

TradingView × modern wealth management × AI Copilot

35. New Sidebar
SMARTPORTFOLIO


⌂ Dashboard


PORTFOLIO
  Holdings
  Transactions
  P&L
  Dividends
  Portfolio Health


INTELLIGENCE
  AI Copilot
  AI Signals
  Portfolio Review
  Risk Radar


RESEARCH
  Stocks
  Screener
  Watchlist
  Market
  News


ANALYTICS
  Stock Analysis
  Simulator
  What-if
  Performance
  Benchmark


TRADING
  Broker Accounts
  Orders
  Positions
  Trade History


ALERTS


SETTINGS
36. Navigation Philosophy

Avoid making users go:

Portfolio
→ Stock
→ Analysis
→ AI
→ Prediction

Instead:

Every important object should be one click away.

From a holding:

HDFCBANK
│
├─ Overview
├─ Performance
├─ Fundamentals
├─ Technical
├─ AI Analysis
├─ Transactions
└─ Simulator
37. Home Screen Priority

The dashboard should answer five questions immediately:

1. How much do I have?

₹24.82L

2. How am I performing?

+14.2%

3. How risky is my portfolio?

63 / 100

4. What changed?

3 important changes

5. What should I investigate?

2 opportunities + 1 risk

That should be the entire philosophy of the home page.

38. MVP Scope

I recommend not rebuilding everything simultaneously.

MVP V2
Must Have
New dashboard
Portfolio engine
Transaction ledger
Accurate average price
Realized/unrealized P&L
XIRR
Holdings
Stock intelligence
Quant score
AI analysis
Portfolio health
Risk radar
Simulator
Watchlist
AI signals
Should Have
Benchmarking
Alerts
Prediction tracking
News
Screener
Later
Broker integration
Order execution
Mobile app
Advisor dashboard
Multi-user/family portfolio
39. Recommended Development Sequence

I would rebuild your existing application in this order:

Sprint 1 — Design System
New navigation
Theme
Typography
Components
Tables
Cards
Charts
AI components
Sprint 2 — Portfolio Core
Portfolio
Holdings
Transactions
Average price
P&L
XIRR
Sprint 3 — Dashboard
Portfolio KPIs
Performance
Allocation
Benchmark
Portfolio health
Sprint 4 — Stock Intelligence
Stock page
Fundamentals
Technical
Valuation
Quant score
Sprint 5 — AI
AI analysis
Portfolio review
AI Copilot
Signals
Explainability
Sprint 6 — Simulator
Buy-more simulator
Portfolio allocation simulator
What-if scenarios
Sprint 7 — Risk
Risk radar
Concentration
Correlation
Drawdown
Portfolio optimization
Sprint 8 — Alerts / Prediction Tracking
AI prediction history
Accuracy
Alerts
Notifications
40. V2 Acceptance Criteria

The product should be considered successful when a user can:

 Import/create a portfolio
 Add transactions
 See accurate average price
 See realized P&L
 See unrealized P&L
 See XIRR
 Compare portfolio against NIFTY
 Understand sector exposure
 Understand portfolio risk
 Open any stock
 See fundamental/technical/valuation scores
 See AI decision
 Understand why AI produced the decision
 See confidence
 Simulate buying more
 Simulate selling
 See resulting average price
 See allocation impact
 Ask AI questions about the portfolio
 Receive meaningful alerts
 See historical AI prediction accuracy
41. The Most Important Product Change

I would change the central user journey from:

Create Portfolio
       ↓
AI Analysis
       ↓
Prediction

to:

MY REAL PORTFOLIO
       ↓
WHAT IS HAPPENING?
       ↓
WHY IS IT HAPPENING?
       ↓
WHAT IS THE RISK?
       ↓
WHAT ARE MY OPTIONS?
       ↓
WHAT IF I BUY / SELL?
       ↓
AI DECISION SUPPORT
       ↓
MONITOR

That is the fundamental redesign.

42. Final Product Positioning

I would ultimately brand the product around:

SmartPortfolio
AI-powered portfolio intelligence.

Know your portfolio. Understand your risk. Make better decisions.

And the four core pillars:

Pillar	Product
Track	Portfolio + P&L
Understand	Research + AI
Simulate	What-if + allocation
Improve	Risk + AI signals
My recommendation for your existing QuantAnalysis

Do not rewrite the entire application from zero.

Instead, treat the current application as V1 backend/data foundation + prototype UI and perform a controlled V2 transformation:

CURRENT QUANTANALYSIS
        │
        ├── KEEP
        │    Existing data integrations
        │    AI integrations
        │    Portfolio calculations where reliable
        │    Existing stock analysis
        │
        ├── REFACTOR
        │    Data model
        │    Portfolio engine
        │    AI architecture
        │    Prediction engine
        │
        └── REDESIGN
             Dashboard
             Navigation
             Holdings
             Stock Intelligence
             AI Copilot
             Risk
             Simulator
             Signals

The highest-priority work is not the AI model. It is building a rock-solid Portfolio Engine underneath the new UI. Once transaction → holding → average cost → P&L → risk → quant score is reliable, the AI layer becomes much more powerful and trustworthy.

One other reason to design the architecture this way: SEBI's current framework explicitly recognizes automated/AI tools and places significant responsibility on regulated entities for AI-derived advice, while also emphasizing suitability, disclosure and records. So building an auditable Data → Quant → Decision → AI Explanation chain now is strategically better than building an opaque "AI predicts stock" engine.

Recommended next artifact

The next thing I would create is not another generic PRD. It should be a V2 implementation specification containing:

Complete screen inventory — ~25 screens
Screen-by-screen wireframe/layout
Existing screen → new screen mapping
PostgreSQL schema
API specification
Quant scoring formulas
AI agent/tool architecture
Prompt architecture
Market-data requirements
Portfolio/P&L calculation rules
Simulator formulas
Alert engine
AI prediction tracking
Role/permission model
V2 phased development backlog