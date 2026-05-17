# Crypto Sentiment Bot 🤖📈

A Python-based automated buy/sell signal generator that combines technical analysis indicators with sentiment analysis to produce actionable trading signals for cryptocurrency markets.

## Overview

This bot integrates multiple signal sources — technical indicators and market sentiment — to generate buy, sell, or hold recommendations. Designed for BTC/USDT and XMR/USDT pairs with extensibility to other assets.

## Features

- **Technical Indicators:** RSI, MACD, Bollinger Bands, EMA crossover signals
- **Sentiment Analysis:** NLP-based parsing of market news and social signals
- **Signal Generation:** Composite buy/sell/hold output based on weighted indicator scoring
- **Live Data Integration:** Real-time price feeds via CoinGecko and exchange APIs
- **Logging:** Trade signal history with timestamps for backtesting review

## Tech Stack

- **Language:** Python
- **Libraries:** Pandas, NumPy, NLTK / TextBlob, Requests, TA-Lib
- **APIs:** CoinGecko, CME Group

## How to Run

```bash
git clone https://github.com/drodutola/crypto-sentiment-bot
cd crypto-sentiment-bot
pip install -r requirements.txt
python bot.py
```

## Signal Logic

| Indicator | Bullish Signal | Bearish Signal |
|---|---|---|
| RSI | < 30 (oversold) | > 70 (overbought) |
| MACD | Bullish crossover | Bearish crossover |
| Bollinger Bands | Price at lower band | Price at upper band |
| Sentiment | Positive score > threshold | Negative score > threshold |

## Author

**Dr. Peter Odutola, M.D.** — Physician, AI developer, and quantitative researcher.  
[GitHub Profile](https://github.com/drodutola)
