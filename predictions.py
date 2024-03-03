from regressor import model
from create_data import get_data_for_gameweek
import pickle

import pandas as pd
import csv


def predict_for_gameweek(gameweek):
    gameweek_data = get_data_for_gameweek(gameweek)

    with open('saved_encoder.pkl', 'rb') as f:
        encoder = pickle.load(f) 
        encoded_features = encoder.transform(gameweek_data[['home_or_away_id', 'opposition_id']])
        encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out())

        data_for_prediction = gameweek_data.drop(['home_or_away_id', 'opposition_id'], axis=1)
        data_for_prediction = pd.concat([data_for_prediction, encoded_df], axis=1)

        data_for_prediction = data_for_prediction.drop('fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('gameweek', axis=1)

        print("dfp=", data_for_prediction)
        predictions = model.predict(data_for_prediction)

        # Add predictions back to the DataFrame
        gameweek_data['predicted_points'] = predictions
    return gameweek_data

gameweek_predictions = predict_for_gameweek(26) 
filename = 'predictionsGW26.csv'

with open(filename, 'w', newline='') as csvfile: 
    writer = csv.writer(csvfile) 
    gameweek_predictions.to_csv(csvfile, mode='a', index=False)
