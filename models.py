import hashlib, pickle, os, csv
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import precision_score, recall_score, f1_score, make_scorer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.utils import class_weight
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler



import xgboost as xgb
from xgboost import XGBClassifier, plot_importance

def prep_test_or_train_data(data_csv):
    """
    Take a csv of data, makes it into a pandas dataframe,
    adjusts the content to make it appropriate for training a model
    and returns the features, target variable and column names from the
    original data
    """
    data_components = {}
    data = pd.read_csv(data_csv)

    #dropping rows with no win odds which happens when a player has moved clubs
    cleaned_data = data.dropna(subset=['win_odds'])

    #drop rows where player has played under 60 minutes
    filtered_data = cleaned_data[cleaned_data['minutes'] >= 60]

    print('Loading data and dropping rows with no win_odds and fewer than 60 mins played')

    # Select relevant features
    features = cleaned_data[['position_id',
                            'player_value',
                            'home_or_away_id',
                            'opposition_team_strength',
                            'team_strength',
                            'recent_points',
                            'recent_bps',
                            'season_points',
                            'season_bps',
                            'season_minutes',
                            'win_odds',
                            'over_two_point_five_goals'
                            ]]
    
    #target variable                        
    target = cleaned_data['over_four_points']
    
    # Encode categorical features
    print('Encoding home or away and position id')
    encoder = OneHotEncoder(handle_unknown='ignore') 
    encoded_features = encoder.fit_transform(features[['home_or_away_id', 'position_id']])

    # Save the encoder
    with open('saved_encoder.pkl', 'wb') as f:  # Choose a suitable filename
        pickle.dump(encoder, f)
    
    # Convert features to DataFrame before merging 
    encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out()) # Convert sparse array to DataFrame

    features = features.reset_index(drop=True)
    encoded_df = encoded_df.reset_index(drop=True)

    features = pd.concat([features, encoded_df], axis=1)

    features = features.drop(columns=['position_id', 'home_or_away_id']) 


    column_names = features.columns 

    scaler = StandardScaler()
    #features = scaler.fit_transform(features)

    data_components['features'] = features
    data_components['column_names'] = column_names
    data_components['target'] = target

    return data_components

def train_XGBoost_classifier_model(training_data_csv):
    """
    Takes a CSV of processed data, processes it further and trains an XGBoost model on it.
    Returns the trained model and the original column names.
    """
    training_data = prep_test_or_train_data(training_data_csv)

    best_params = {'colsample_bytree': 0.1, 'learning_rate': 3, 'max_depth': 3, 'n_estimators': 200, 'reg_alpha': 10, 'reg_lambda': 10, 'subsample': 0.1}


    """
    the below can be used for debugging what the model is actually trained on
    """

    with open('actual_training.csv', 'w', newline='') as csvfile: 
        features_df = training_data['features']
        target_series = training_data['target']
        target_series = target_series.reset_index(drop=True) 
        combined_df = pd.concat([pd.DataFrame(features_df, columns=training_data['column_names']), target_series], axis=1)
        writer = csv.writer(csvfile)

        combined_df.to_csv(csvfile, mode='a', index=False)
    

    print('Training Model')

    X_train = training_data['features']
    y_train = training_data['target']

    oversample = SMOTE(sampling_strategy=0.8) 
    undersample = RandomUnderSampler(sampling_strategy=0.98)  

    X_resampled, y_resampled = oversample.fit_resample(X_train, y_train)
    X_resampled, y_resampled = undersample.fit_resample(X_resampled, y_resampled)

    model = XGBClassifier()  
    model.fit(X_resampled, y_resampled) 


    feature_names = model.get_booster().feature_names
    print('feature names = ', feature_names)

    return {'model': model, 'original_column_names': training_data['column_names']}

def tune_XGBoost_model(training_data):
    """
    Tries different hyperparamters of a model and prints
    the best combination.
    """

    param_grid = {
    'learning_rate': [3, 5, 9], 
    'max_depth': [3,6,9], 
    'n_estimators': [5,50,200], 
    'reg_alpha': [2, 6, 10],  
    'reg_lambda': [2, 6, 10],
    'subsample': [0.1, 1, 2],
    'colsample_bytree': [0.1, 0.5, 0.9] 
    } 
    
    def custom_scorer(y_true, y_pred):
        recall = recall_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        return 0.3 * recall + 0.7 * precision  
        

    my_custom_scorer = make_scorer(custom_scorer) 



    xgb_model = XGBClassifier()  
    grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, cv=5, scoring=my_custom_scorer, verbose=1)

    test_data = prep_test_or_train_data('./processed_data/testing_data.csv')

    grid_search.fit(test_data['features'], test_data['target']) 

    best_model = grid_search.best_estimator_
    
    print(grid_search.best_params_)

    return None

def save_model(model, original_column_names):
    """
    Takes a trained model and the data it was trained on
    and saves it for future use
    """
    model_hash = hashlib.sha256(pickle.dumps(model)).hexdigest()

    model_filename = 'trained_XGBoost_model.pkl'
    folder_path = 'trained_models'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = os.path.join(folder_path, model_filename) 

    with open(filepath, 'wb') as f:
        pickle.dump({'model': model, 'hash': model_hash, 'column_names': original_column_names}, f)

    print(f'model saved to {filepath}')
    return None

def load_and_verify_model(model_filename):
    with open(model_filename, 'rb') as f:
        data = pickle.load(f)
        model = data['model']
        stored_hash = data['hash']


    # Recalculate hash
    current_hash = hashlib.sha256(pickle.dumps(model)).hexdigest()
    print('Checking the loaded model is the same one that has been saved')
    if current_hash != stored_hash:
        raise ValueError("Loaded model doesn't match the original model!")

    return model

def test_model(trained_model, testing_data_csv):
    """
    Takes file paths of a trained model and data to test it with.
    Tests the given model on the given data and prints the results.
    """
    print(f'Loading trained model from {trained_model}')
    model = load_and_verify_model(trained_model)

    print('Loading test data')
    test_data = prep_test_or_train_data('./processed_data/testing_data.csv')

    print('testing model')
    predictions = model.predict(test_data['features'])
    precision = precision_score(test_data['target'], predictions)
    recall = recall_score(test_data['target'], predictions)
    f1 = f1_score(test_data['target'], predictions)

    importance_dict = model.get_booster().get_score(importance_type='gain')

    for i in importance_dict:
        print(i, importance_dict[i])
    
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1-Score:", f1)

    return None

def train_and_save_XGBoost_classifier_model():
    """
    Takes a CSV of processed data, processes it further and trains an XGBoost model on it.
    Then saves it.
    """
    trained_model = train_XGBoost_classifier_model('./processed_data/training_data.csv')
    save_model(trained_model['model'], trained_model['original_column_names'])
    return None
