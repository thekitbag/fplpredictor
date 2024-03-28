import hashlib, pickle, os

from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
from xgboost import XGBClassifier, plot_importance

from processors import prep_test_or_train_data

def train_XGBoost_classifier_model(training_data_csv):
    """
    Takes a CSV of processed data, processes it further and trains an XGBoost model on it.
    Returns the trained model and the original column names.
    """
    training_data = prep_test_or_train_data(training_data_csv)

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
    feature_names = model.get_booster().feature_names
    print(feature_names)

    return {'model': model, 'original_column_names': training_data['column_names']}

def tune_XGBoost_model(training_data):
    """
    Tries different hyperparamters of a model and prints
    the best combination.
    """
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
