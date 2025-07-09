import joblib # Used for loading pre-trained machine learning models
import pandas as pd # Data manipulation library, used for creating DataFrames
from ML_model.latest_data import get_latest_btc_input # Custom function to fetch the latest data for prediction input

# Load the pre-trained Random Forest Regressor model from the specified path.
# This avoids retraining the model every time a prediction is needed.
model = joblib.load("ML_model/model_btc_e.pkl")

# Define an asynchronous function to handle Bitcoin price prediction requests.
# 'bot' is the Telegram Bot API instance, 'user_id' is the chat ID to send the message to.
async def predict_btc(bot , user_id):
    # Call a custom function to get the most recent Bitcoin market data.
    # This data will serve as input features for the ML model.
    latest_data = get_latest_btc_input()

    # Convert the dictionary of latest data into a Pandas DataFrame.
    # The ML model expects its input in a DataFrame format with feature columns matching its training.
    input_df = pd.DataFrame([latest_data])

    # Fill any potential NaN (Not a Number) values in the input DataFrame with 0.0.
    # This ensures the model receives clean numerical input, as NaN values can cause errors.
    input_df = input_df.fillna(0.0)

    # Use the loaded ML model to make a prediction on the prepared input data.
    # .predict() returns an array, so [0] extracts the single predicted value.
    prediction = model.predict(input_df)[0]

    # Construct the message string to be sent to the user via Telegram.
    # It includes the predicted close price and the latest snapshot of market data.
    # f-strings are used for easy formatting, and :,.2f formats the float to 2 decimal places with comma separator.
    message = (
        f"*📈 Bitcoin Price Prediction*\n\n"
        f"💰 *Predicted Close:* ${prediction:,.2f}\n\n"
        f"*Market Snapshot:*\n"
        f"• Open: ${latest_data.get('open', 'N/A')}\n" # Using .get() with default 'N/A' for robustness
        f"• High: ${latest_data.get('high', 'N/A')}\n"
        f"• Low: ${latest_data.get('low', 'N/A')}\n"
        f"• Volume: {latest_data.get('volume', 'N/A')}\n"
    )

    # Send the formatted message back to the user via the Telegram bot.
    # chat_id specifies where the message goes, text is the message content.
    await bot.send_message(chat_id=user_id ,text=message )

    # Return the predicted price for potential further use in the application logic.
    # The directional prediction (up/down) would be derived here if needed for return.
    return prediction