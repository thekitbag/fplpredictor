import pandas as pd
import os, csv
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from handlers import get_fpl_bootstrap_data, get_fpl_fixtures_data, get_fpl_gameweek_live_data 



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
    
    #target variable                        
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

def get_data_for_gameweeks(start_gameweek, end_gameweek):
    """
    Gets all of the data needed for given gameweeks and returns it in a single dictionary
    """
    all_data = {'gameweeks': []}
    bootstrap_data = get_fpl_bootstrap_data()
    fixtures_data = get_fpl_fixtures_data()
    all_data['bootstrap_data'] = bootstrap_data
    all_data['fixtures_data'] = fixtures_data
    for i in range(start_gameweek, end_gameweek+1):
        gameweeks_dict = {}
        gameweek_data = get_fpl_gameweek_live_data(i)
        gameweeks_dict['gameweek'] = i
        gameweeks_dict['performances'] = gameweek_data
        all_data['gameweeks'].append(gameweeks_dict)
    
    return all_data

def get_player_value(player_id, bootstrap_data):
    """
    Takes a player id and the bootstrap data, looks the 
    id up in the bootstrap data and returns the players FPL
    value as an integer
    """
    player = next((player for player in bootstrap_data['elements'] if player['id'] == player_id), None)
    value = player['now_cost']
    return value

def get_player_name(player_id, bootstrap_data):
    """
    Takes a player id and the bootstrap data nad returns
    the player's name
    """
    player = next((player for player in bootstrap_data['elements'] if player['id'] == player_id), None)
    name = player['second_name']
    return name

def get_team_data(player_id, bootstrap_data):
    """
    Takes a player id and the bootstrap data nad returns
    the player's team name
    """
    team_data = {}
    player = next((player for player in bootstrap_data['elements'] if player['id'] == player_id), None)
    team_id = player['team']
    team = next((team for team in bootstrap_data['teams'] if team['id'] == team_id))
    team_name = team['name']
    team_data['team_name'] = team_name
    team_data['team_id'] = team_id
    return team_data

def get_opposition_name_and_id(player, fixture_data, bootstrap_data):
    """
    takes a player's gameweek data the fixture data and the bootstrap data.
    uses the fixture_id and the was_home flag to find opposotion in the fixtures data
    then gets opposition name from the bootstrap data
    """
    opposition_data = {}
    fixture_id = player['explain'][0]['fixture'] if len(player['explain']) > 0 else -1 #players without a club will have nothing in explain list
    
    if fixture_id == -1:
        opposition_data['opposition_id'] = -1
        opposition_data['home_or_away_id'] = -1
        opposition_data['opposition_name'] = 'NULL'
        return opposition_data

    player_static_data = next((p for p in bootstrap_data['elements'] if p['id'] == player['id']), None)
    team_id = player_static_data['team']
    fixture_data = next((fixture for fixture in fixture_data if fixture['id'] == fixture_id), None)

    if fixture_data['team_h'] == team_id:
        opposition_data['home_or_away_id'] = 1
        opposition_id = fixture_data['team_a']
    else:
        opposition_data['home_or_away_id'] = 2
        opposition_id = fixture_data['team_h']
    opposition_data['opposition_id'] = opposition_id

    opposition_team_data = next((team for team in bootstrap_data['teams'] if team['id'] == opposition_id), None)
    opposition_name = opposition_team_data['name']
    opposition_data['opposition_name'] = opposition_name

    return opposition_data




        


def clean_and_interpret_data(gameweeks_and_static_dict):
    """
    Takes a dictionary of aggregated JSON from various calls
    to FPL APIs, grabs the datapoints that matter, works out new datapoints
    and returns a single dictionary with all of the data needed
    """
    clean_and_interpreted_data_dict = {'performances': []}

    gameweeks = gameweeks_and_static_dict['gameweeks']
    fixtures = gameweeks_and_static_dict['fixtures_data']
    bootstrap = gameweeks_and_static_dict['bootstrap_data']

    for gw in gameweeks:
        for player in gw['performances']['elements']:
            gameweek = gw['gameweek']
            player_id = player['id']
            value = get_player_value(player_id, bootstrap)  

            player_name = get_player_name(player_id, bootstrap)
            team_name = get_team_data(player_id, bootstrap)['team_name']
            opposition_info = get_opposition_name_and_id(player, fixtures, bootstrap)
            opposition_name = opposition_info['opposition_name']
            fixture_id = player['explain'][0]['fixture'] if len(player['explain']) > 0 else -1
            home_or_away_id = opposition_info['home_or_away_id']
            minutes = player['stats']['minutes']
            opposition_id = opposition_info['opposition_id']

            opposition_team_strength = 4

            team_id = get_team_data(player_id, bootstrap)['team_id']
            team_strength = 5

            recent_points = 19
            recent_bps = 69

            season_points = 101
            season_bps = 288

            win_odds = 1.3

            over_four_points = 1 
            points = player['stats']['total_points']

            clean_and_interpreted_data_dict['performances'].append(
                {
                    'gameweek': gameweek,
                    'player_id': player_id,
                    'value': value,
                    #names that will be dropped before model runs
                    'player_name': player_name,
                    'team_name': team_name,
                    'opposition_name': opposition_name,
                    #this week info
                    'fixture_id': fixture_id,
                    'home_or_away_id': home_or_away_id,
                    'minutes': minutes, 
                    'opposition_id': opposition_id,
                    'opposition_team_strength': opposition_team_strength,
                    #team info
                    'team_id': team_id,
                    'team_strength': team_strength,
                    #recent form
                    'recent_points': recent_points,
                    'recent_bps': recent_bps,
                    #season form
                    'season_points': season_points,
                    'season_bps': season_bps,
                    #odds_data
                    'win_odds': win_odds,
                    #target_variables
                    'over_four_points': over_four_points,
                    'points': points,

                }
            )


    return clean_and_interpreted_data_dict


def aggregate_data(gameweeks_dict):
    """
    Takes an dictionary of aggregated clean and intrepreted data and combines it
    into a single pandas dataframe
    """
    gameweeks_df = pd.DataFrame(gameweeks_dict)
    print('gw_df', gameweeks_df.head(), gameweeks_df.columns)
    return gameweeks_df

def save_data_csv(gameweeks_df, filename):
    """
    Takes gameweeks dataframe and saves it with the given filename
    """
    folder_path = 'processed_data'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = os.path.join(folder_path, filename) 

    with open(filepath, 'w', newline='') as csvfile: 
        writer = csv.writer(csvfile)
        print(f'saving data for  to {filepath}')
        gameweeks_df.to_csv(csvfile, mode='a', index=False)
    
    return None


def create_data_for_gameweeks(start_gameweek, end_gameweek, filename):
    """
    Gets the data for the chosen gameweeks, cleans it, interprets it
    puts it into a single dataframe and saves it with the given filename
    """
    all_gameweeks = get_data_for_gameweeks(start_gameweek, end_gameweek)
    clean_and_interpreted_data_dict = clean_and_interpret_data(all_gameweeks)
    performances = clean_and_interpreted_data_dict['performances']
    gameweeks_df = aggregate_data(performances)
    save_data_csv(gameweeks_df, filename)
    print(f"CSV saved wiith filename {filename}")
    return None
          

create_data_for_gameweeks(2,3,'test1.csv')

