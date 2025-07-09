# Crypto Risk Management & Forecasting Bot

A real-time cryptocurrency risk monitoring and forecasting system that combines:
- Live spot price tracking via the Bybit API
- Auto-hedging actions using user-defined thresholds
- Machine learning-based BTC price forecasting using Random Forest
- Telegram bot integration for interactive notifications and commands

---

## 🔧 Project Structure

```
Crypto-Risk-Bot/
│
├── ml/                        # Machine Learning price prediction module
│   ├── model.py              # Random Forest model code
│   ├── btc_2015_2024.csv     # BTC historical price & indicator data
│   └── utils.py              # Data preprocessing helpers
│
├── riskEngine/
│   ├── risk_monitor.py       # Price threshold/risk detection logic
│   ├── hedge.py              # Auto hedge execution logic
│   └── risk_metrics.py       # Delta, VaR, drawdown, etc.
│
├── exchanges/
│   └── bybit.py              # API integration for live spot prices
│
├── TeligramBot/
│   ├── bot.py                # Telegram bot init and command router
│   ├── handlers.py           # Telegram bot command logic
│   └── config.py             # Stores user positions and risk config
│
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── main.py                   # Entry point to run the bot
```

---

## 🚀 Features

- 📉 Real-time monitoring of crypto positions with entry vs. current price tracking
- 🔔 Auto-alerts on Telegram when risk thresholds are breached
- 🤖 Auto-hedging logic using Bybit or other exchanges (mock/demo in this project)
- 📊 Risk metrics: Delta, Notional exposure, Max Drawdown, VaR
- 🔮 Machine Learning forecasting of BTC close prices using Random Forest
- 📥 Logs of price history and hedge actions for auditability

---

## 🧠 ML Forecasting (in `ml/` folder)

- Dataset: `btc_2015_2024.csv` with BTC OHLCV + indicators
- Model: RandomForestRegressor from scikit-learn
- Output: Next-day BTC price prediction (used for Telegram insights)

### Sample Code:
```python
model = RandomForestRegressor()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

---

## 🛠 Setup & Run

### 1. Clone Repo
```bash
git clone https://github.com/prashantdubeypng/goquanttask.git
cd goquanttask
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Telegram Bot
- Create a bot via BotFather
- Save the API token in `TeligramBot/config.py`

### 4. Run the Bot
```bash
python main.py
```

---

## 📦 Requirements

```txt
pandas
numpy
matplotlib
scikit-learn
python-telegram-bot
requests
```

---

## 📸 Screenshots
- Telegram Alert on Breach
- ML Forecast Plot (actual vs predicted)

---

## 📬 Contact
**Prashant Dubey**  
Email: prashant2107pd@gmail.com  
LinkedIn: [linkedin.com/in/21prashant](https://linkedin.com/in/21prashant)

---

## 📄 License
MIT License
