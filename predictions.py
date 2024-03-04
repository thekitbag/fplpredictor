from regressor import model
from create_data import get_data_for_gameweek
import pickle

import pandas as pd
import csv


def predict_for_gameweek(gameweek):
    gameweek_data = get_data_for_gameweek(gameweek)

    with open('saved_encoder.pkl', 'rb') as f:
        #Encoding opposition and home or away IDs
        encoder = pickle.load(f) 
        encoded_features = encoder.transform(gameweek_data[['home_or_away_id', 'opposition_id']])
        encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out())
        data_for_prediction = gameweek_data.drop(['home_or_away_id', 'opposition_id'], axis=1)
        data_for_prediction = pd.concat([data_for_prediction, encoded_df], axis=1)

        #Dropping things the model shouldn't see
        data_for_prediction = data_for_prediction.drop('fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('gameweek', axis=1)

        #Dropping strings that the model can't understand
        data_for_prediction = data_for_prediction.drop('player_name', axis=1)
        data_for_prediction = data_for_prediction.drop('opposition_name', axis=1)

        predictions = model.predict(data_for_prediction)

        # Add predictions back to the DataFrame
        gameweek_data['predicted_points'] = predictions

        # Add
    return gameweek_data

gameweek_predictions = predict_for_gameweek(26) 
filename = 'predictionsGW26.csv'

with open(filename, 'w', newline='') as csvfile: 
    writer = csv.writer(csvfile)
    output_data = gameweek_predictions[['player_name', 'opposition_name', 'fpl_points', 'predicted_points']]
    output_data = output_data.sort_values(by='predicted_points', ascending=False)
    output_data.to_csv(csvfile, mode='a', index=False)
