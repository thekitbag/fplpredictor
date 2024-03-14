import requests

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
GAMEWEEK_URL_START = f"https://fantasy.premierleague.com/api/event/"

def get_fpl_bootstrap_data():
    """
    gets the data from the FPL Bootstrap API and returns it
    """
    response = requests.get(BOOTSTRAP_URL)
    response.raise_for_status()  
    bootstrap_data = response.json() 
    return bootstrap_data

def get_fpl_gameweek_live_data(gameweek_id):
    """
    Takes an gameweek Id , gets the data from the FPL Gameweek Live API
    and returns it
    """
    url = GAMEWEEK_URL_START + str(gameweek_id) + '/live/'
    response = requests.get(url)
    response.raise_for_status()  
    gameweek_data = response.json() 
    return gameweek_data
    

def get_fpl_fixtures_data():
    """
    gets the data from the FPL Fixtures API and returns it
    """
    response = requests.get(FIXTURES_URL)
    response.raise_for_status()  
    fixtures_data = response.json() 
    return fixtures_data
