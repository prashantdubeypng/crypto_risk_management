import os

for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))


# STEP 1: Import Libraries
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# STEP 2: Load Data
btc_df = pd.read_csv("/kaggle/input/bitcoin-price-trends-with-indicators-8-years/btc_2015_2024.csv")

# STEP 3: Preprocess
btc_df['date'] = pd.to_datetime(btc_df['date'])  # Corrected column name
btc_df = btc_df.sort_values('date')
btc_df = btc_df.dropna()

# STEP 4: Feature Engineering
# We'll predict 'close' using all other numeric features
features = btc_df.drop(columns=['date', 'close'])  # drop target + date
target = btc_df['close']

# STEP 5: Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# STEP 6: Train Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# STEP 7: Evaluate
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"RMSE: {rmse:.2f}")

# STEP 8: Plot Predictions
plt.figure(figsize=(12, 6))
plt.plot(y_test.values, label="Actual Price")
plt.plot(y_pred, label="Predicted Price")
plt.title("Bitcoin Price Prediction (Random Forest)")
plt.xlabel("Samples")
plt.ylabel("Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

