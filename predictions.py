import os
import csv
import pickle
import pandas as pd


from processors import create_gameweeks_dataframe, create_future_gameweeks_df


NEXT_GAMEWEEK = 30 #used to determine whether dealing with historic data or constructing future data

def prep_data_for_prediction(gameweek_data):
    """
    Takes gameweek data, encodes columns and drops columns
    that will bias or break the model
    """

    with open('saved_encoder.pkl', 'rb') as f:
        #Encoding opposition and home or away IDs
        encoder = pickle.load(f) 
        encoded_features = encoder.transform(gameweek_data[['home_or_away_id', 'position_id']])
        encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out())
        gameweek_data.drop(['home_or_away_id', 'position_id'], axis=1)
        gameweek_data.reset_index(drop=True, inplace=True)  # Reset the index
        data_for_prediction = pd.concat([gameweek_data, encoded_df], axis=1)

        #Dropping things the model shouldn't see
        data_for_prediction = data_for_prediction.drop('minutes', axis=1)
        data_for_prediction = data_for_prediction.drop('points', axis=1)
        data_for_prediction = data_for_prediction.drop('over_four_points', axis=1)
        data_for_prediction = data_for_prediction.drop('gameweek', axis=1)

        #Dropping strings that the model can't understand
        data_for_prediction = data_for_prediction.drop('player_name', axis=1)
        data_for_prediction = data_for_prediction.drop('opposition_name', axis=1)
        data_for_prediction = data_for_prediction.drop('team_name', axis=1)

        return data_for_prediction


def make_gameweek_predictions(model_filepath, gameweek_data):
    """
    Takes preprocessed and prepped gameweek data and the filepath of a saved model and uses the saved model
    to make predictions and returns a dataframe with the given predictions
    """

    data_for_prediction = prep_data_for_prediction(gameweek_data)
    
    print('loading model')
    with open(model_filepath, 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        column_names = model_data['column_names']

        data_for_prediction = data_for_prediction[column_names]

        predictions_proba = model.predict_proba(data_for_prediction)

        # Add probabilities of being a high-scorer
        gameweek_data['predicted_high_scorer'] = predictions_proba[:, 1]  # Assuming the 2nd column is for high-scorer

        return gameweek_data

def predict_gameweek(gameweek):
    """
    Takes a gameweek, fetches data for it and uses a pre-trained model to
    makes predictions on the outcomes of it. Outputs a CSV which shows the 
    predictions and the actual points scored
    """
    print('fetching gameweek data')
    if gameweek < NEXT_GAMEWEEK:
        gameweek_data = create_gameweeks_dataframe(gameweek, gameweek)
    else:
        gameweek_data = create_future_gameweeks_df(gameweek)
    gameweek_predictions = make_gameweek_predictions('./trained_models/trained_XGBoost_model.pkl', gameweek_data)
    filename = f'predictionsGW{gameweek}.csv'

    folder_path = 'predictions'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = f'predictionsGW{gameweek}.csv'
    filepath = os.path.join(folder_path, filename) 

    with open(filepath, 'w', newline='') as csvfile: 
        writer = csv.writer(csvfile)
        output_data = gameweek_predictions[['player_name', 'opposition_name', 'points', 'predicted_high_scorer']]
        output_data = output_data.sort_values(by='predicted_high_scorer', ascending=False)
        print(f'saving predictions for gameweek {gameweek} to {filepath}')

        output_data.to_csv(csvfile, mode='a', index=False)
    
    return None
