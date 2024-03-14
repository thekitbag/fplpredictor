import pandas as pd
from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
from xgboost import XGBClassifier, plot_importance
import pickle
import hashlib
import os

def prep_test_or_train_data(data_csv):
    data_components = {}
    data = pd.read_csv(data_csv)
    cleaned_data = data.dropna(subset=['win_odds'])

    print('Loading data and dropping rows with no win_odds')

    # Select relevant features
    features = cleaned_data[['team_id',
                            'position_id', 
                            'kickoff_time', 
                            'home_or_away_id', 
                            'opposition_id', 
                            'overall_team_strength',
                            'team_position_relevant_strength',
                            'recent_points',
                            'recent_bps',
                            'recent_influence',
                            'recent_creativity',
                            'recent_threat',
                            'recent_xx',
                            'season_points',
                            'season_bps',
                            'season_influence',
                            'season_creativity',
                            'season_threat',
                            'season_xx',
                            'win_odds',
                            '>2.5'
                            ]]
    target = cleaned_data['over_four_fpl_points']
    # Encode categorical features
    print('Encoding home or away and opposition IDs')
    encoder = OneHotEncoder(handle_unknown='ignore') 
    encoded_features = encoder.fit_transform(features[['home_or_away_id', 'opposition_id']])

    # Convert features to DataFrame before merging 
    encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out()) # Convert sparse array to DataFrame

    features = features.reset_index(drop=True)
    encoded_df = encoded_df.reset_index(drop=True)

    features = pd.concat([features, encoded_df], axis=1)

    column_names = features.columns 

    scaler = StandardScaler()
    features = scaler.fit_transform(features)

    data_components['features'] = features
    data_components['column_names'] = column_names
    data_components['target'] = target

    return data_components


def train_and_save_model(model_filename):

    training_data = prep_test_or_train_data('./processed_data/training_data.csv')

    model = XGBClassifier(learning_rate=0.1, max_depth=7, n_estimators=200, scale_pos_weight= 12.0)
    
    best_params = {'colsample_bytree': 0.9, 'learning_rate': 0.15, 'max_depth': 6, 'n_estimators': 300, 'reg_alpha': 0.1, 'reg_lambda': 0.1, 'subsample': 0.7}

    learning_rate = best_params['learning_rate']
    max_depth = best_params['max_depth']
    n_estimators = best_params['n_estimators']
    reg_alpha = best_params['reg_alpha']
    reg_lambda = best_params['reg_lambda']
    subsample = best_params['subsample']
    colsample_bytree = best_params['colsample_bytree']

    model = XGBClassifier(learning_rate=learning_rate, max_depth=max_depth, n_estimators=n_estimators, 
                      reg_alpha=reg_alpha, reg_lambda=reg_lambda, subsample=subsample, 
                      colsample_bytree=colsample_bytree) 
    
    print('Training Model')
    model.fit(training_data['features'], training_data['target'])

    model_hash = hashlib.sha256(pickle.dumps(model)).hexdigest()

    folder_path = 'trained_models'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = os.path.join(folder_path, model_filename) 

    with open(filepath, 'wb') as f:
        pickle.dump({'model': model, 'hash': model_hash, 'column_names': training_data['column_names']}, f)

    print(f'model saved to {filepath}')
    return None


def test_model(model_filename):
    print(f'Loading trained model from {model_filename}')
    model = load_and_verify_model(model_filename)

    print('Loading test data')
    test_data = prep_test_or_train_data('./processed_data/testing_data.csv')

    print('testing model')
    predictions = model.predict(test_data['features'])
    precision = precision_score(test_data['target'], predictions)
    recall = recall_score(test_data['target'], predictions)
    f1 = f1_score(test_data['target'], predictions)

    print('features:', model.get_booster().feature_names)

    importance_dict = model.get_booster().get_score(importance_type='gain')
    for i in importance_dict:
        print(i, importance_dict[i])
    
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1-Score:", f1)

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

def tune_model():
    
    param_grid = {
    'learning_rate': [0.05, 0.1, 0.15], 
    'max_depth': [4, 5, 6], 
    'n_estimators': [200, 300, 400],
    'reg_alpha': [0.01, 0.05, 0.1], 
    'reg_lambda': [0.1, 0.2, 0.3], 
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.8, 0.9, 1.0]
    }

    xgb_model = XGBClassifier()  
    grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, cv=5, scoring='f1', verbose=1)

    test_data = prep_test_or_train_data('./processed_data/testing_data.csv')

    grid_search.fit(test_data['features'], test_data['target']) 

    best_model = grid_search.best_estimator_
    
    print(grid_search.best_params_)


#train_and_save_model('trained_XGBoost_classifier_model.pkl')
#test_model('./trained_models/trained_XGBoost_classifier_model.pkl')
#tune_model()
