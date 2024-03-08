import json
import pandas as pd
import requests
import csv
import time
from datetime import datetime, timedelta

# Configuration
HUMAN_READABLE_NAMES = False
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"

response = requests.get(BOOTSTRAP_URL)
response.raise_for_status()  

bootstrap_data = response.json()
teams_df = pd.DataFrame(bootstrap_data['teams']) 
players_df = pd.DataFrame(bootstrap_data['elements'])
events_df = pd.DataFrame(bootstrap_data['events'])
phases_df = pd.DataFrame(bootstrap_data['phases'])
element_types_df = pd.DataFrame(bootstrap_data['element_types'])
odds_df = pd.read_csv('./data/historic_odds.csv')


response = requests.get(FIXTURES_URL)
response.raise_for_status() 
fixtures_data = response.json()
fixtures_df = pd.DataFrame(fixtures_data)

def getPlayerNameFromPlayerId(id):
    player_data = players_df.loc[players_df['id'] == id]
    if not player_data.empty:
        first_name = player_data['first_name'].iloc[0]
        second_name = player_data['second_name'].iloc[0]
        return f"{first_name} {second_name}"
    else:
        return "Player Not Found"

def getPlayerTeamFromPlayerId(id):
    resp = {}
    player_data = players_df.loc[players_df['id'] == id]
    team_data = teams_df.loc[teams_df['id'] == player_data['team'].iloc[0]]
    team_name = team_data['name'].iloc[0]
    team_id = team_data['id'].iloc[0]
    resp['team_name'] = team_name
    resp['team_id'] = team_id
    resp['strength_overall_home'] = team_data['strength_overall_home'].iloc[0]
    resp['strength_overall_away'] = team_data['strength_overall_away'].iloc[0]
    resp['strength_attack_home'] = team_data['strength_attack_home'].iloc[0]
    resp['strength_attack_away'] = team_data['strength_attack_away'].iloc[0]
    resp['strength_defence_home'] = team_data['strength_defence_home'].iloc[0]
    resp['strength_defence_away'] = team_data['strength_defence_away'].iloc[0]
    return resp

def getPlayerPositionFromPlayerId(id):
    resp = {}
    player_data = players_df.loc[players_df['id'] == id]
    position_id = player_data['element_type'].iloc[0]
    position_data = element_types_df.loc[element_types_df['id'] == position_id]
    position_name = position_data['singular_name_short'].iloc[0]
    resp['position_id'] = position_id
    resp['position_name'] = position_name
    return resp

def getkickoffTimeFromFixtureId(id):
    fixture_data = fixtures_df.loc[fixtures_df['id'] == id]

    if not fixture_data.empty:
        kickoff = fixture_data['kickoff_time'].iloc[0]
        kickoff = pd.to_datetime(kickoff)
        hour_of_day = kickoff.hour
        return hour_of_day
    else:
        print(f"Warning: Fixture ID {id} not found")  # More informative message
        return None  # Or a default placeholder value
    
def getHomeOrAwayDataFromIds(playerId, fixtureId):
    resp = {}
    player_data = players_df.loc[players_df['id'] == playerId]
    fixture_data = fixtures_df.loc[fixtures_df['id'] == fixtureId]

    if fixture_data['team_h'].iloc[0] == player_data['team'].iloc[0]:
        resp['home_or_away'] = "Home"
        resp['home_or_away_id'] = 1
        team_data = teams_df.loc[teams_df['id'] == fixture_data['team_a'].iloc[0]]
        team_name = team_data['name'].iloc[0]
        team_id = team_data['id'].iloc[0]
        resp['opposition'] = team_name
        resp['opposition_id'] = team_id
    elif fixture_data['team_a'].iloc[0] == player_data['team'].iloc[0]:
        resp['home_or_away'] = "Away"
        resp['home_or_away_id'] = 2
        team_data = teams_df.loc[teams_df['id'] == fixture_data['team_h'].iloc[0]]
        team_name = team_data['name'].iloc[0]
        team_id = team_data['id'].iloc[0]
        resp['opposition'] = team_name
        resp['opposition_id'] = team_id
    else:
        resp['home_or_away'] = "NULL"
        resp['home_or_away_id'] = 0
        resp['opposition'] = "NULL"
        resp['opposition_id'] = 0

    return resp

def getTeamOddsFromIds(playerId, fixtureId):
    resp = {}
    player_data = players_df.loc[players_df['id'] == playerId]
    fixture_data = fixtures_df.loc[fixtures_df['id'] == fixtureId]
    odds_data = odds_df

    if fixture_data['team_h'].iloc[0] == player_data['team'].iloc[0]:
        team_data = teams_df.loc[teams_df['id'] == fixture_data['team_h'].iloc[0]]
        team_name = team_data['name'].iloc[0]
        datetime_obj = datetime.strptime(fixture_data['kickoff_time'].iloc[0], '%Y-%m-%dT%H:%M:%SZ')
        new_date_str = datetime_obj.strftime('%d/%m/%Y')
        games_on_this_day = odds_data.loc[(odds_data['Date'] == new_date_str)]
        specific_game = games_on_this_day.loc[(games_on_this_day['HomeTeam'] == team_name)]

        if not specific_game.empty:  # Check if any matching game was found
            win_odds = specific_game['B365H'].iloc[0]
            over_two_point_five = specific_game['B365>2.5'].iloc[0]
            resp['win_odds'] = win_odds
            resp['>2.5'] = over_two_point_five
            return resp
        else:
            resp['win_odds'] = "NULL"
            resp['>2.5'] = "NULL"
            return resp
    
    if fixture_data['team_a'].iloc[0] == player_data['team'].iloc[0]:
        team_data = teams_df.loc[teams_df['id'] == fixture_data['team_a'].iloc[0]]
        team_name = team_data['name'].iloc[0]
        datetime_obj = datetime.strptime(fixture_data['kickoff_time'].iloc[0], '%Y-%m-%dT%H:%M:%SZ')
        new_date_str = datetime_obj.strftime('%d/%m/%Y')
        games_on_this_day = odds_data.loc[(odds_data['Date'] == new_date_str)]
        specific_game = games_on_this_day.loc[(games_on_this_day['AwayTeam'] == team_name)]

        if not specific_game.empty:  # Check if any matching game was found
            win_odds = specific_game['B365A'].iloc[0]
            over_two_point_five = specific_game['B365>2.5'].iloc[0]
            resp['win_odds'] = win_odds
            resp['>2.5'] = over_two_point_five
            return resp
        else:
            resp['win_odds'] = "NULL"
            resp['>2.5'] = "NULL"
            return resp
    resp['win_odds'] = "NULL"
    resp['>2.5'] = "NULL"
    return resp
        
def get_previous_four_weeks_data(gameweek):
    all_data = [] 
    for i in range(gameweek - 4, gameweek - 1):
        resp = {}
        response = requests.get(f"https://fantasy.premierleague.com/api/event/{i}/live/")
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['elements'])  # Create a DataFrame
        all_data.append(df)
    combined_df = pd.concat(all_data, ignore_index=True)  # Concatenate DataFrames
    return combined_df

def get_season_data(gameweek):
    all_data = [] 
    for i in range(1, gameweek):
        resp = {}
        response = requests.get(f"https://fantasy.premierleague.com/api/event/{i}/live/")
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['elements'])  # Create a DataFrame
        all_data.append(df)
        time.sleep(0.2)
    combined_df = pd.concat(all_data, ignore_index=True)  # Concatenate DataFrames
    return combined_df

def get_previous_weeks_performance(player_id, previous_weeks_data):
    resp = {}
    player_history = previous_weeks_data.loc[previous_weeks_data['id'] == player_id]

    total_points = 0
    total_bps = 0
    total_influence = 0
    total_creativity = 0
    total_threat = 0
    total_xg = 0
    total_xa = 0
    total_xgi = 0
    total_xgc = 0
    for index, row in player_history.iterrows():
        points = row['stats']['total_points']
        total_points += points
        bps = row['stats']['bps']
        total_bps += bps
        influence = row['stats']['influence']
        total_influence += float(influence)
        creativity = row['stats']['creativity']
        total_creativity += float(creativity)
        threat = row['stats']['threat']
        total_threat += float(threat)
        xg = row['stats']['expected_goals']
        total_xg += float(xg)
        xa = row['stats']['expected_assists']
        total_xa += float(xa)
        xgi = row['stats']['expected_goal_involvements']
        total_xgi += float(xgi)
        xgc = row['stats']['expected_goals_conceded']
        total_xgc += float(xgc) 

    resp['total_points'] = total_points
    resp['total_bps'] = total_bps
    resp['total_influence'] = total_influence
    resp['total_creativity'] = total_creativity
    resp['total_threat'] = total_threat
    resp['total_xg'] = total_xg
    resp['total_xa'] = total_xa
    resp['total_xgi'] = total_xgi
    resp['total_xgc'] = total_xgc

    return  resp

def get_data_for_gameweek(gameweek):
    gw_data = []
    response = requests.get(f"https://fantasy.premierleague.com/api/event/{gameweek}/live/")
    response.raise_for_status()
    data = response.json()

    #we get the earlier season data for all players outside of the loop to avoid doing it for every player
    previous_four_weeks_data = get_previous_four_weeks_data(gameweek)
    season_data = get_season_data(gameweek)

    for player in data['elements']:
        if len(player['explain']) > 0:
            home_or_away_data = getHomeOrAwayDataFromIds(player['id'], player['explain'][0]['fixture'])
            team_data = getPlayerTeamFromPlayerId(player['id'])
            odds_data = getTeamOddsFromIds(player['id'], player['explain'][0]['fixture'])

            #inside the loop we find the past weeks data for the individual player
            previous_weeks_performance = get_previous_weeks_performance(player['id'], previous_four_weeks_data)
            season_performance = get_previous_weeks_performance(player['id'], season_data)

            player_data = {
                #FPL Static Data
                'gameweek': gameweek,
                'player_id': player['id'], 
                'player_name': getPlayerNameFromPlayerId(player['id']),
                'team_id': team_data['team_id'],
                'strength_overall_home': team_data['strength_overall_home'],
                'strength_overall_away': team_data['strength_overall_away'],
                'strength_attack_home': team_data['strength_attack_home'],
                'strength_attack_away': team_data['strength_attack_away'],
                'strength_defence_home': team_data['strength_defence_home'],
                'strength_defence_away': team_data['strength_defence_away'],
                'position_id': getPlayerPositionFromPlayerId(player['id'])['position_id'],
                #Fixture Data
                'kickoff_time': getkickoffTimeFromFixtureId(player['explain'][0]['fixture']),
                'home_or_away_id':  home_or_away_data['home_or_away_id'],
                'opposition_id': home_or_away_data['opposition_id'],
                'opposition_name': home_or_away_data['opposition'],
                #Recent Form
                'recent_points': previous_weeks_performance['total_points'],
                'recent_bps': previous_weeks_performance['total_bps'],
                'recent_influence': previous_weeks_performance['total_influence'],
                'recent_creativity': previous_weeks_performance['total_creativity'],
                'recent_threat': previous_weeks_performance['total_threat'],
                'recent_xg': previous_weeks_performance['total_xg'],
                'recent_xa': previous_weeks_performance['total_xa'],
                'recent_xgi': previous_weeks_performance['total_xgi'],
                'recent_xgc': previous_weeks_performance['total_xgc'],
                #Season_form
                'season_points': season_performance['total_points'],
                'season_bps': season_performance['total_bps'],
                'season_influence': season_performance['total_influence'],
                'season_creativity': season_performance['total_creativity'],
                'season_threat': season_performance['total_threat'],
                'season_xg': season_performance['total_xg'],
                'season_xa': season_performance['total_xa'],
                'season_xgi': season_performance['total_xgi'],
                'season_xgc':season_performance['total_xgc'], 
                #Odds Data
                'win_odds': odds_data['win_odds'],
                '>2.5': odds_data['>2.5'],
                #Target Variables: 
                'minutes': player['stats']['minutes'],
                'fpl_points': player['stats']['total_points'],
                'over_four_fpl_points': 1 if player['stats']['total_points'] > 4 else 0
                
            }
            gw_data.append(player_data)
    gw_df = pd.DataFrame(gw_data)
    gw_df = gw_df[gw_df['minutes'] >= 60] 

    return gw_df



def create_csv(START_GAMEWEEK, END_GAMEWEEK, filename):

    with open(filename, 'w', newline='') as csvfile: 
        writer = csv.writer(csvfile) 

        for gameweek in range(START_GAMEWEEK, END_GAMEWEEK + 1):
            gameweek_df = get_data_for_gameweek(gameweek)
            header = gameweek == START_GAMEWEEK  # Add header only for the first write  
            gameweek_df.to_csv(csvfile, mode='a', index=False, header=header)

create_csv(21, 25, "test_data.csv")


