from create_data import get_data_for_gameweek
from classifier import prep_test_or_train_data, load_and_verify_model
import pickle

import pandas as pd
import csv
import os


def predict_for_gameweek(gameweek, column_names):
    gameweek_data = get_data_for_gameweek(gameweek)

    with open('saved_encoder.pkl', 'rb') as f:
        #Encoding opposition and home or away IDs
        encoder = pickle.load(f) 
        encoded_features = encoder.transform(gameweek_data[['home_or_away_id', 'opposition_id']])
        encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out())
        gameweek_data.drop(['home_or_away_id', 'opposition_id'], axis=1)
        gameweek_data.reset_index(drop=True, inplace=True)  # Reset the index
        data_for_prediction = pd.concat([gameweek_data, encoded_df], axis=1)

        #Dropping things the model shouldn't see
        data_for_prediction = data_for_prediction.drop('minutes', axis=1)
        data_for_prediction = data_for_prediction.drop('fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('over_four_fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('gameweek', axis=1)

        #Dropping strings that the model can't understand
        data_for_prediction = data_for_prediction.drop('player_name', axis=1)
        data_for_prediction = data_for_prediction.drop('opposition_name', axis=1)

        data_for_prediction = data_for_prediction[column_names]
 
        with open('./trained_models/trained_classifier_model.pkl', 'rb') as f:
            model = pickle.load(f)

            # Add probabilities of being a high-scorer
            gameweek_data['predicted_high_scorer'] = predictions_proba[:, 1]  # Assuming the 2nd column is for high-scorer

            return gameweek_data

def predict_historic_gameweek(gameweek):

    column_names = prep_test_or_train_data('./processed_data/testing_data.csv')['column_names'] #hack

    gameweek_predictions = predict_for_gameweek(gameweek, column_names) 
    filename = f'predictionsGW{gameweek}.csv'

    with open(filename, 'w', newline='') as csvfile: 
        writer = csv.writer(csvfile)
        output_data = gameweek_predictions[['player_name', 'opposition_name', 'fpl_points', 'predicted_high_scorer']]
        output_data = output_data.sort_values(by='predicted_high_scorer', ascending=False)
        output_data.to_csv(csvfile, mode='a', index=False)
    
    return None

def predict_future_gameweek(gameweek):
    gameweek_data = pd.read_csv(f'./processed_data/gameweek{gameweek}_data.csv')
    #column_names = prep_test_or_train_data('./processed_data/testing_data.csv')['column_names'] #hack
    
    with open('saved_encoder.pkl', 'rb') as f:
        #Encoding opposition and home or away IDs
        encoder = pickle.load(f) 
        encoded_features = encoder.transform(gameweek_data[['home_or_away_id', 'opposition_id']])
        encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out())
        gameweek_data.drop(['home_or_away_id', 'opposition_id'], axis=1)
        gameweek_data.reset_index(drop=True, inplace=True)  # Reset the index
        data_for_prediction = pd.concat([gameweek_data, encoded_df], axis=1)

        #Dropping things the model shouldn't see
        data_for_prediction = data_for_prediction.drop('player_id', axis=1)
        data_for_prediction = data_for_prediction.drop('minutes', axis=1)
        data_for_prediction = data_for_prediction.drop('fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('over_four_fpl_points', axis=1)
        data_for_prediction = data_for_prediction.drop('gameweek', axis=1)

        #Dropping strings that the model can't understand
        data_for_prediction = data_for_prediction.drop('player_name', axis=1)
        data_for_prediction = data_for_prediction.drop('opposition_name', axis=1)

        model_filename = './trained_models/trained_XGBoost_classifier_model.pkl'

        with open(model_filename, 'rb') as f:
            data = pickle.load(f)
            model = data['model']
            column_names = data['column_names']
            data_for_prediction = data_for_prediction[column_names]
            
            predictions_proba = model.predict_proba(data_for_prediction)

            # Add probabilities of being a high-scorer
            gameweek_data['predicted_high_scorer'] = predictions_proba[:, 1] # Assuming the 2nd column is for high-scorer

            folder_path = 'predictions'
            filename = f'predictionsGW{gameweek}.csv'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            filepath = os.path.join(folder_path, filename) 

            with open(filepath, 'w', newline='') as csvfile: 
                writer = csv.writer(csvfile) 
                output_data = gameweek_data[['player_name', 'opposition_name', 'predicted_high_scorer']]
                output_data = output_data.sort_values(by='predicted_high_scorer', ascending=False)
                output_data.to_csv(csvfile, mode='a', index=False)

predict_future_gameweek(28)
#predict_historic_gameweek(27)
