# StockLens SDK

StockLens SDK is an AI-powered toolkit for stock sentiment and trend analysis.

## Features
- Fetch and analyze stock market sentiment
- Generate human-like summaries
- Convert summaries to speech
- Predict short-term market trend

## Installation
```bash
pip install stocklens-sdk

Usage
from stocklens_sdk import analyze_sentiment, generate_summary, generate_audio

summary = generate_summary("Apple reported strong quarterly earnings.")
audio = generate_audio(summary, "AAPL")
print(summary, audio)


---

## 🧮 STEP 5 — Build the package

Run these commands from your project root:

```bash
pip install build twine
python -m build


This will create a dist/ folder containing:

dist/
├── stocklens_sdk-1.0.0.tar.gz
└── stocklens_sdk-1.0.0-py3-none-any.whl