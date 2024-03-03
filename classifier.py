import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV

data = pd.read_csv('FPL_and_odds_data_numeric.csv')
cleaned_data = data.dropna(subset=['win_odds'])

# Select relevant features
features = cleaned_data[['player_id', 
                        'position_id', 
                        'kickoff_time', 
                        'home_or_away_id', 
                        'opposition_id', 
                        'win_odds',
                        'strength_overall_home',
                        'strength_overall_away',
                        'strength_attack_home',
                        'strength_attack_away',
                        'strength_defence_home',
                        'strength_defence_away',
                        'recent_minutes',
                        'recent_points',
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

column_names = features.columns 

scaler = StandardScaler()
features = scaler.fit_transform(features)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

from xgboost import XGBClassifier

scale_pos_weight = 12 / 1

param_grid = {
    'scale_pos_weight': [scale_pos_weight],  # Start with the calculated value
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5, 7],
    'n_estimators': [100, 200, 300]
}

model = XGBClassifier(learning_rate=0.1, max_depth=7, n_estimators=200, scale_pos_weight= 12.0)
 
model.fit(X_train, y_train) 

predictions = model.predict(X_test)
precision = precision_score(y_test, predictions)
recall = recall_score(y_test, predictions)
f1 = f1_score(y_test, predictions)

print("Precision:", precision)
print("Recall:", recall)
print("F1-Score:", f1)



