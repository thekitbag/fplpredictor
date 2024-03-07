import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
from xgboost import XGBClassifier, plot_importance
import pickle

def prep_test_or_train_data(data_csv):
    data_components = {}
    data = pd.read_csv(data_csv)
    cleaned_data = data.dropna(subset=['win_odds'])

    # Select relevant features
    features = cleaned_data[['player_id',
                            'team_id',
                            'position_id', 
                            'kickoff_time', 
                            'home_or_away_id', 
                            'opposition_id', 
                            'strength_overall_home',
                            'strength_overall_away',
                            'strength_attack_home',
                            'strength_attack_away',
                            'strength_defence_home',
                            'strength_defence_away',
                            'recent_points',
                            'total_bps',
                            'total_influence',
                            'total_creativity',
                            'total_threat',
                            'total_xg', 
                            'total_xa',
                            'total_xgi',
                            'total_xgc',
                            'win_odds',
                            '>2.5'
                            ]]
    target = cleaned_data['over_four_fpl_points']
    # Encode categorical features
    encoder = OneHotEncoder(handle_unknown='ignore') 
    encoded_features = encoder.fit_transform(features[['home_or_away_id', 'opposition_id']])

    # Convert features to DataFrame before merging 
    encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out()) # Convert sparse array to DataFrame

    features = features.reset_index(drop=True)
    encoded_df = encoded_df.reset_index(drop=True)
    features = pd.concat([features, encoded_df], axis=1)

    print(features.columns)

    column_names = features.columns 

    scaler = StandardScaler()
    features = scaler.fit_transform(features)

    data_components['features'] = features
    data_components['column_names'] = column_names
    data_components['target'] = target

    return data_components


def train_and_save_model(model_filename):

    training_data = prep_test_or_train_data('train_data.csv')

    model = XGBClassifier(learning_rate=0.1, max_depth=7, n_estimators=200, scale_pos_weight= 12.0)
    
    model.fit(training_data['features'], training_data['target']) 

    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)
    print(f'model saved with filename {model_filename}')
    return None


def test_model(model_filename):
    with open(model_filename, 'rb') as f:
        model = pickle.load(f)

        test_data = prep_test_or_train_data('test_data.csv')

        predictions = model.predict(test_data['features'])
        precision = precision_score(test_data['target'], predictions)
        recall = recall_score(test_data['target'], predictions)
        f1 = f1_score(test_data['target'], predictions)

        importance_dict = model.get_booster().get_score(importance_type='gain')
        print(importance_dict)

        plot_importance(model) 

        print("Precision:", precision)
        print("Recall:", recall)
        print("F1-Score:", f1)

        return None


#train_and_save_model('trained_classifier_model.pkl')
test_model('trained_classifier_model.pkl')
