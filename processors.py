import pandas as pd
import os, csv
from random import randint
from datetime import datetime
from handlers import get_fpl_bootstrap_data, get_fpl_fixtures_data, get_fpl_gameweek_live_data 

def get_data_for_gameweeks():
    """
    Gets all of the data needed for given gameweeks and returns it in a single dictionary
    """
    all_data = {'gameweeks': []}
    bootstrap_data = get_fpl_bootstrap_data()
    fixtures_data = get_fpl_fixtures_data()
    all_data['bootstrap_data'] = bootstrap_data
    all_data['fixtures_data'] = fixtures_data
    print("getting all gameweeks data")
    for i in range(1, 29):
        print(f'gameweek {i}')
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
    Takes a player id and the bootstrap data and returns
    the player's name
    """
    player = next((player for player in bootstrap_data['elements'] if player['id'] == player_id), None)
    name = player['second_name']
    return name

def get_player_position_id(player_id, bootstrap_data):
    """
    Takes a player ID and the bootstrap data and returns the player's
    position ID
    """
    player = next((player for player in bootstrap_data['elements'] if player['id'] == player_id), None)
    position_id = player['element_type']
    return position_id

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
    team_strength = (team['strength_overall_home'] + team['strength_overall_away']) / 2
    team_data['team_name'] = team_name
    team_data['team_id'] = team_id
    team_data['team_strength'] = team_strength
    return team_data

def get_opposition_info(player, fixture_data, bootstrap_data):
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
        opposition_data['opposition_strength'] = -1
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
    opposition_team_strength = (opposition_team_data['strength_overall_home'] + opposition_team_data['strength_overall_away']) / 2
    opposition_data['opposition_strength'] = opposition_team_strength

    return opposition_data


def get_recent_performances(player_id, current_gameweek_id, gameweeks):
    """
    Gets the players performances from the gameweeks
    data for the last 4 gameweeks and returns their
    points and BPS
    """
    recent_gameweeks_data = [gw for gw in gameweeks if gw['gameweek'] in range(current_gameweek_id-3, current_gameweek_id)]
    recent_performances_data = {'recent_points': 0, 'recent_bps': 0}
    for gw in recent_gameweeks_data:
        players = gw['performances']['elements']
        player = next((player for player in players if player['id'] == player_id), 0)
        if player == 0:
            recent_performances_data = {'recent_points': -1, 'recent_bps': -1}
            return recent_performances_data
        points = player['stats']['total_points']
        recent_performances_data['recent_points'] += points / 3 #to get average
        bps = player['stats']['bps']
        recent_performances_data['recent_bps'] += bps / 3 #to get average
    return recent_performances_data

def get_season_performances(player_id, current_gameweek_id, gameweeks_data):
    """
    Gets the players performances from all of the gameweeks
    data for the last 4 gameweeks and returns their
    points and BPS
    """
    season_performances_data = {'season_points': 0, 'season_bps': 0, 'season_minutes': 0}
    season_averages = {'avg_points':0, 'avg_bps': 0, 'avg_minutes': 0}
    gameweeks = [gw for gw in gameweeks_data if gw['gameweek'] < current_gameweek_id]
    for gw in gameweeks:
        players = gw['performances']['elements']
        player = next((player for player in players if player['id'] == player_id), 0)
        if player == 0:
            season_averages = {'avg_points':-1, 'avg_bps': -1, 'avg_minutes': -1}
            return season_averages
        points = player['stats']['total_points']
        season_performances_data['season_points'] += points 
        bps = player['stats']['bps']
        season_performances_data['season_bps'] += bps
        minutes = player['stats']['minutes']
        season_performances_data['season_minutes'] += minutes
    season_averages['avg_points'] = season_performances_data['season_points'] / len(gameweeks)
    season_averages['avg_bps'] = season_performances_data['season_bps'] / len(gameweeks)
    season_averages['avg_minutes'] = season_performances_data['season_minutes'] / len(gameweeks)
    return season_averages

def get_team_odds(team_info, fixture_id, bootstrap_data, fixtures_data):
    odds_data_dict = {}
    
    odds_data = pd.read_csv('./raw_data/historic_odds.csv')

    player_team_id = team_info['team_id']
    player_team_name = team_info['team_name']

    fixture_data = next((fixture for fixture in fixtures_data if fixture['id'] == fixture_id), None)
    
    if fixture_data == None:
        odds_data_dict['win_odds'] = -1
        odds_data_dict['>2.5'] = -1
        return odds_data_dict
    
    if fixture_data['team_h'] == player_team_id:
        datetime_obj = datetime.strptime(fixture_data['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ')
        new_date_str = datetime_obj.strftime('%d/%m/%Y')
        games_on_this_day = odds_data.loc[(odds_data['Date'] == new_date_str)]
        specific_game = games_on_this_day.loc[(games_on_this_day['HomeTeam'] == player_team_name)]

        if not specific_game.empty:  # Check if any matching game was found
            win_odds = specific_game['B365H'].iloc[0]
            over_two_point_five = specific_game['B365>2.5'].iloc[0]
            odds_data_dict['win_odds'] = win_odds
            odds_data_dict['>2.5'] = over_two_point_five
            return odds_data_dict
        else:
            odds_data_dict['win_odds'] = -1
            odds_data_dict['>2.5'] = -1
            return odds_data_dict
    
    if fixture_data['team_a'] == player_team_id:
        datetime_obj = datetime.strptime(fixture_data['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ')
        new_date_str = datetime_obj.strftime('%d/%m/%Y')
        games_on_this_day = odds_data.loc[(odds_data['Date'] == new_date_str)]
        specific_game = games_on_this_day.loc[(games_on_this_day['AwayTeam'] == player_team_name)]

        if not specific_game.empty:  # Check if any matching game was found
            win_odds = specific_game['B365A'].iloc[0]
            over_two_point_five = specific_game['B365>2.5'].iloc[0]
            odds_data_dict['win_odds'] = win_odds
            odds_data_dict['>2.5'] = over_two_point_five
            return odds_data_dict
        else:
            odds_data_dict['win_odds'] = -1
            odds_data_dict['>2.5'] = -1
            return odds_data_dict
    odds_data_dict['win_odds'] = -1
    odds_data_dict['>2.5'] = -1
    return odds_data_dict

def interpret_player_data(players, gameweeks_and_static_dict, gameweek, clean_and_interpreted_data_dict):
    """
    Takes a dictionary of players, some static data and a destination dictionary. Loops through the players
    interprets it with the help of some helper functions, puts it into a dictionary and add the dictionary to
    the destination dictionary
    """
    fixtures = gameweeks_and_static_dict['fixtures_data']
    bootstrap = gameweeks_and_static_dict['bootstrap_data']
    all_gameweeks = gameweeks_and_static_dict['gameweeks']
    #Calling functions that combine the three data sources and return them nicely
    print('getting player info for each week')
    for player in players:
        #p = player['id']
        #print(f'player {p}')
        opposition_info = get_opposition_info(player, fixtures, bootstrap)
        team_info = get_team_data(player['id'], bootstrap)
        recent_performances = get_recent_performances(player['id'], gameweek, all_gameweeks)
        season_performances = get_season_performances(player['id'], gameweek, all_gameweeks)
        fixture_id = player['explain'][0]['fixture'] if len(player['explain']) > 0 else -1
        odds_data = get_team_odds(team_info, fixture_id, bootstrap, fixtures)
        #Setting the variables that will be added to the dictionary that is returned
        player_id = player['id']
        player_value = get_player_value(player['id'], bootstrap)  
        player_name = get_player_name(player['id'], bootstrap)
        player_position_id = get_player_position_id(player['id'], bootstrap)
        team_name = team_info['team_name']
        opposition_name = opposition_info['opposition_name']
        fixture_id = fixture_id
        home_or_away_id = opposition_info['home_or_away_id']
        minutes = player['stats']['minutes']
        opposition_id = opposition_info['opposition_id']
        opposition_team_strength = opposition_info['opposition_strength']
        team_id = team_info['team_id']
        team_strength = team_info['team_strength']
        recent_points = recent_performances['recent_points']
        recent_bps = recent_performances['recent_bps']
        season_points = season_performances['avg_points']
        season_bps = season_performances['avg_bps']
        season_minutes = season_performances['avg_minutes']
        win_odds = odds_data['win_odds']
        over_two_point_five_goals = odds_data['>2.5']
        over_four_points = 1 if player['stats']['total_points'] > 4 else 0
        points = player['stats']['total_points']

        #Creating the dictionary that will be returned inside clean_and_interpreted_data_dict
        clean_and_interpreted_data_dict['performances'].append(
            {
                'gameweek': gameweek,
                #player info
                'player_id': player_id,
                'player_value': player_value,
                'position_id': player_position_id,
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
                'season_minutes': season_minutes,
                #odds_data
                'win_odds': win_odds,
                'over_two_point_five_goals': over_two_point_five_goals,
                #target_variables
                'over_four_points': over_four_points,
                'points': points,
            }
        )


def clean_and_interpret_data(gameweeks_and_static_dict, start_gameweek, end_gameweek):
    """
    Takes a dictionary of aggregated JSON from various calls
    to FPL APIs, grabs the datapoints that matter, works out new datapoints
    and returns a single dictionary with all of the data needed
    """
    clean_and_interpreted_data_dict = {'performances': []}
    all_gameweeks = gameweeks_and_static_dict['gameweeks']
    gameweeks = [gw for gw in all_gameweeks if gw['gameweek'] in range(start_gameweek, end_gameweek+1)]

    for gw in gameweeks:
        players = gw['performances']['elements']
        interpret_player_data(players, gameweeks_and_static_dict, gw['gameweek'], clean_and_interpreted_data_dict)
    return clean_and_interpreted_data_dict

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

def create_gameweeks_dataframe(start_gameweek, end_gameweek):
    """
    Takes the dictionary of clean interpreted data and turns it into a dataframe.
    used in run.py to pull the data in before making predictions
    """
    all_gameweeks = get_data_for_gameweeks()
    clean_and_interpreted_data_dict = clean_and_interpret_data(all_gameweeks, start_gameweek, end_gameweek)
    performances = clean_and_interpreted_data_dict['performances']
    df = pd.DataFrame(performances)
    return df

def create_data_for_gameweeks(start_gameweek, end_gameweek, filename):
    """
    Gets the data for the chosen gameweeks, cleans it, interprets it
    puts it into a single dataframe and saves it with the given filename
    """
    all_gameweeks = get_data_for_gameweeks()
    clean_and_interpreted_data_dict = clean_and_interpret_data(all_gameweeks, start_gameweek, end_gameweek)
    performances = clean_and_interpreted_data_dict['performances']
    gameweeks_df = pd.DataFrame(performances)
    save_data_csv(gameweeks_df, filename)
    print(f"CSV saved wiith filename {filename}")
    return None

def get_fixture_id(fixtures, player_team_id, gameweek):
    """
    Takes fixtures, a player Id and a gameweek number and returns the fixture id for
    that player in that gameweek
    """
    team_fixtures = [fixture for fixture in fixtures if fixture['team_h'] == player_team_id or fixture['team_a'] == player_team_id]
    gameweek_fixture = next(fixture for fixture in team_fixtures if fixture['event'] == gameweek)
    return gameweek_fixture['id']
    
def create_future_gameweeks_df(gameweek):
    resp = {'performances': []}
    all_gameweeks_data = get_data_for_gameweeks()
    fixtures = all_gameweeks_data['fixtures_data']
    bootstrap = all_gameweeks_data['bootstrap_data']
    all_gameweeks = all_gameweeks_data['gameweeks']
    #players = all_gameweeks[0]['performances']['elements']
    players = []
    for player in bootstrap['elements']:
        if player['total_points'] > 50:
            player_team_id = player['team']
            player_stats = {
                            "id": player['id'],
                            "stats": {
                                "minutes": 0,
                                "total_points": 0
                                },
                            "explain": [
                                {
                                "fixture": get_fixture_id(fixtures, player_team_id, gameweek),
                                "stats": [
                                        {
                                        "identifier": "minutes",
                                        "points": 0,
                                        "value": 0
                                        }
                                    ]
                                }
                                ]
                            }
            players.append(player_stats)

    interpret_player_data(players, all_gameweeks_data, gameweek, resp)
    df = pd.DataFrame(resp['performances'])
 
    return df