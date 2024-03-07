import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor 
from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV
import pickle  # Or joblib 

data = pd.read_csv('FPL_and_odds_data_numeric.csv')
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
target = cleaned_data['fpl_points']

# Encode categorical features
encoder = OneHotEncoder(handle_unknown='ignore') 
encoded_features = encoder.fit_transform(features[['home_or_away_id', 'opposition_id']])

with open('saved_encoder.pkl', 'wb') as f:
    pickle.dump(encoder, f)  

# Convert features to DataFrame before merging 
encoded_df = pd.DataFrame(encoded_features.toarray(), columns=encoder.get_feature_names_out()) # Convert sparse array to DataFrame

features = features.reset_index(drop=True)
encoded_df = encoded_df.reset_index(drop=True)
features = pd.concat([features, encoded_df], axis=1)

column_names = features.columns # Store the column names

# Optional: Scale features (try it if it helps the model)
scaler = StandardScaler()
features = scaler.fit_transform(features)

features = pd.DataFrame(features, columns=column_names)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# Train Decision Tree with limited depth

model = RandomForestRegressor(max_depth=8, min_samples_split=10, n_estimators=200, random_state=42)
model.fit(X_train, y_train)  # Train on the full training set

with open('trained_regressor_model.pkl', 'wb') as f:
    pickle.dump(model, f)


predictions = model.predict(X_test)


# Evaluating the Performance
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("Mean Squared Error:", mse)
print("R-squared:", r2)

importances = model.feature_importances_

for feature, importance in zip(column_names, importances):
    print(f'{feature}: {importance}')

