from __future__ import print_function
import httplib2
import os
import pickle
import string

from apiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from copy import copy
from time import sleep

# Constants for checkboxed sheets
RANGE_START = "A1"
RANGE_END = "M200"

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
SHEET_CRED_FILE = 'sheets.googleapis.com-python-quickstart.json'
DRIVE_CRED_FILE = 'drive.json'
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

# from Google Sheets API v4 Python quickstart


def get_credentials(filename):
    creds = None
    # The file  stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(filename):
        with open(filename, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(filename, 'wb') as token:
            pickle.dump(creds, token)
    return creds


credentials = get_credentials(DRIVE_CRED_FILE)
discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                'version=v4')

service = discovery.build('sheets', 'v4', credentials=credentials,
                          discoveryServiceUrl=discoveryUrl)

sheets = service.spreadsheets()

# comp
# scoresheet_id = "1kghfpm1Z1e_OYIAjVH29wHwKiA0THv45_6rbiwP0vSg"
# standard
scoresheet_id = "1bUOVvP6eOXx7t5cWQVBvSvk9IzR67mNp6j9PdbYrAvg"


def get_games_from_round(round_num):
    result = sheets.values().get(spreadsheetId=scoresheet_id,
                                 range=f"Round {round_num}!{RANGE_START}:{RANGE_END}").execute()
    values = result.get('values', [])

    games = list()

    # hardcoding in that entries are ten rows tall, and a whole bunch of information about where
    # things are in the entries
    for game_num in range((len(values) + 1) // 10):
        game = values[10 * game_num: 10 * game_num + 8]

        game_rep = {}

        game_rep["room_name"] = game[0][0]
        game_rep["round_num"] = round_num

        # e.g. Amalthea-7
        game_rep["game_id"] = f"{game[0][0]}-{round_num}"

        game_rep["team_1_name"] = game[0][1]
        game_rep["team_2_name"] = game[0][7]

        game_rep["team_1_bp"] = int(game[1][0][6:])
        game_rep["team_2_bp"] = int(game[2][0][6:])

        game_rep["team_1_score"] = int(game[1][1][7:])
        game_rep["team_2_score"] = int(game[1][7][7:])

        game_rep["team_1_players"] = {}
        game_rep["team_2_players"] = {}

        # team 1 players

        for col in range(1, 7):
            player_name = game[2][col]
            if player_name.isspace() or player_name[:-1] == "Player " \
                    or len(game[3]) <= col or game[3][col] == '':
                continue

            game_rep["team_1_players"][player_name] = \
                {"TUH": int(game[3][col]),
                 "15": int(game[4][col]),
                 "10": int(game[5][col]),
                 "-5": int(game[6][col])}

        # team 2 players

        for col in range(7, 13):
            player_name = game[2][col]
            if player_name.isspace() or player_name[:-1] == "Player " \
                    or len(game[3]) <= col or game[3][col] == '':
                continue

            game_rep["team_2_players"][player_name] = \
                {"TUH": int(game[3][col]),
                 "15": int(game[4][col]),
                 "10": int(game[5][col]),
                 "-5": int(game[6][col])}

        game_rep["team_1_bh"] = sum([p["15"] + p["10"]
                                     for p in game_rep["team_1_players"].values()])
        game_rep["team_2_bh"] = sum([p["15"] + p["10"]
                                     for p in game_rep["team_2_players"].values()])

        games.append(game_rep)

    return games


def extract_teams_from_game(game):
    teams = dict()
    teams[game['team_1_name']] = set(game['team_1_players'].keys())
    teams[game['team_2_name']] = set(game['team_2_players'].keys())
    return teams


def extract_teams_from_games(games):
    all_teams = dict()
    for game in games:
        teams = extract_teams_from_game(game)
        for team in teams:
            if team not in all_teams:
                all_teams[team] = teams[team]
            else:
                all_teams[team] = all_teams[team].union(teams[team])
    return all_teams


def lookup_item_in_dict(items, item):
    # an awful hack for which i am very ashamed
    for i, t in enumerate(list(items)):
        if item == t:
            return i


def generate_sqbs_file(tournament_name, games, teams):
    """Number of teams
    For each team:
        1 plus the number of players (i.e., information on how many of the following lines to associate with this team)
        Team name
        Each player name on a separate line. (This leaf node in our documentation represents as many lines as there are players on a given team.)"""

    print(len(teams))
    for team in teams:
        print(1 + len(teams[team]))
        print(team)
        for player in teams[team]:
            print(player)

    """
    Number of matches
    For each match:
        Id
        0-based index of the team shown on the left in the Game Entry screen
        0-based index of the team shown on the right in the Game Entry screen
        Score of left team, or -1 if the game is a forfeit
        Score of right team, or -1 if the game is a forfeit
        Toss-Ups Heard
        Rnd
        """
    print(len(games))
    for game in games:
        print(game["game_id"])
        print(lookup_item_in_dict(teams, game["team_1_name"]))
        print(lookup_item_in_dict(teams, game["team_2_name"]))
        print(game["team_1_score"])
        print(game["team_2_score"])
        print(20)
        print(game["round_num"])

        """
        If bouncebacks are tracked manually:
            ...
        Otherwise:
            left team Bonuses Heard
            left team Bonuses [sic] Pts
            right team Bonuses Heard
            right team Bonuses [sic] Pts
        """
        print(game["team_1_bh"])
        print(game["team_1_bp"])
        print(game["team_2_bh"])
        print(game["team_2_bp"])

        """
        If "Overtime" is checked then 1, otherwise 0
        left team tossups-without-bonuses (the left box following the "Overtime" checkbox)
        right team tossups-without-bonuses (the left box following the "Overtime" checkbox)
        If "Forfeit" is checked then 1, otherwise 0. (In a forfeit, the left team is the winner and the right team is the loser.)
        If "Track Lightning Round Stats" is checked (in tournament setup) then the left team's Ltng Pts, otherwise 0
        If "Track Lightning Round Stats" is checked (in tournament setup) then the right team's Ltng Pts, otherwise 0
        """

        print(0)
        print(0)  # unclear about these two
        print(0)  # unclear about these two
        print(0)
        print(0)
        print(0)

        """
        The following a total of 16 times. It starts with the first player on the left team, then it's the first player on the right team, then the second player on the left team, then the second player on the right team, etc., until each team has had eight players (or all-zero blocks) listed.
            The 0-based index of the player within his/her team (as listed above), or -1 if this slot is not used for a player
            GP (games played) for this player, or 0 if this slot is not used for a player
            Number of questions answered for the first possible point value. If this point value is not used or this slot is not used for a player, then 0. Commonly, this is the number of powers.
            Number of questions answered for the second possible point value. If this point value is not used or this slot is not used for a player, then 0. Commonly, this is the number of regular "gets".
            Number of questions answered for the third possible point value. If this point value is not used or this slot is not used for a player, then 0. Commonly, this is the number of negs.
            Number of questions answered for the fourth possible point value. If this point value is not used or this slot is not used for a player, then 0. Commonly, this is not used and is therefore 0.
            Total points scored by this player, or 0 if this slot is not used for a player.
        """

        team1_players = list(teams[game["team_1_name"]])
        team2_players = list(teams[game["team_2_name"]])

        team1_stats = game["team_1_players"]
        team2_stats = game["team_2_players"]

        for i in range(16):
            real = False
            if i % 2 == 0 and len(team1_players) > (i // 2):
                player = team1_players[i // 2]
                if player in team1_stats:
                    stats = team1_stats[player]
                    real = True
            elif i % 2 == 1 and len(team2_players) > (i // 2):
                player = team2_players[i // 2]
                if player in team2_stats:
                    stats = team2_stats[player]
                    real = True

            if real:
                print(i // 2)
                print(stats["TUH"] / 20)
                print(stats["15"])
                print(stats["10"])
                print(stats["-5"])
                print(0)
                print(15*stats["15"] + 10*stats["10"] - 5*stats["-5"])

            else:
                print(-1)
                print(0)
                print(0)
                print(0)
                print(0)
                print(0)
                print(0)

    """
    If "Bonus Conversion Tracking" (in tournament setup) is "None" then 0, otherwise 1
    If "Bonus Conversion Tracking" (in tournament setup) is "Automatic" then 1, if "None" then 0, if "Manual Hrd, Auto Pts" then 2, if "Manual with Bouncebacks" then 3
    If "Track Power and Neg Stats" is enabled (in tournament setup) then 3, otherwise 2
    If "Track Lightning Round Stats" is enabled (in tournament setup) then 1, otherwise 0
    If "Track Toss-Ups Heard" is enabled (in tournament setup) then 1, otherwise 0
    If "Sort Players by Pts/TUH" is enabled (in the Sorting tab of Settings) then 1, otherwise 0
    A bit mask for the "Warnings" tab in Settings. Start with 0; add 128 if the first is enabled, add 64 if the second is enabled, and so on, up to adding 2 if the seventh is enabled, so 254 represents all warnings enabled.
    """

    print(1)
    print(1)
    print(3)
    print(0)
    print(1)
    print(0)
    print(254)

    """
    If round report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If team standings report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If individual standings report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If scoreboard report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If team detail report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If individual detail report is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If the "stat key" for web reports is enabled (in the Reports tab of Settings) then 1, otherwise 0
    If a custom stylesheet for web reports is specified (in the Reports tab of Settings) then 1, otherwise 0
    If "Use Divisions" is enabled (in the General tab of Settings) then 1, otherwise 0
    The 1-based index of the sort method chosen in the Sorting tab of Settings. (1 is for "Record, PPG", …, 5 is for "Record, Head-to-Head, PPTH")
    """

    print(1)
    print(1)
    print(1)
    print(1)
    print(1)
    print(1)
    print(1)
    print(0)
    print(1)  # <== This is Divisions
    print(1)

    """
    Tournament name
    The Host Address (from the FTP tab of Settings)
    The User Name (from the FTP tab of Settings)
    The Directory (from the FTP tab of Settings)
    The Base File Name (from the FTP tab of Settings)
    If "Always use '/' in paths" in the FTP tab of settings is false, and "British-Style Reports" in the Reports tab of settings is false, then 0. If /-in-paths is true and British is false, then 1. If /-in-paths is false and British is true, then 2. If both are true, then 3. (This is oddly complex; one assumes that this line originally represented just "Always use '/' in paths", then the "British-Style Reports" option was created later and its value incorporated into this line to avoid breaking backward-compatibility.)
    """

    print(tournament_name)
    print("")
    print("")
    print("")
    print("")
    print(0)

    """
    The file suffix next to "Include Team Standings" (in the Reports tab of Settings)
    The file suffix next to "Include Individual Standings" (in the Reports tab of Settings)
    The file suffix next to "Include Scoreboard" (in the Reports tab of Settings)
    The file suffix next to "Include Team Detail" (in the Reports tab of Settings)
    The file suffix next to "Include Individual Detail" (in the Reports tab of Settings)
    The file suffix next to "Include Round Reports" (in the Reports tab of Settings)
    The file suffix next to "Include Stat Key" (in the Reports tab of Settings)
    The file name next to "Use Style Sheet" (in the Reports tab of Settings)
    """

    print("_rounds.html")
    print("_standings.html")
    print("_individuals.html")
    print("_games.html")
    print("_teamdetail.html")
    print("_playerdetail.html")
    print("_statkey.html")
    print("")

    """
    If Divisions [i.e., pools] are used, then the number of Divisions, otherwise 0
    If Divisions are used, then the name of each Division in order (This leaf node in our documentation represents as many lines as there are Divisions, which may be no lines at all.)
    The number of teams
    For each team according to its index, the (0-based) index of the Division it is assigned to, or -1 if Divisions are not used. (This leaf node in our documentation represents as many lines as there are teams.)
    """

    # This is specific to each tournament

    print(4)
    print("Chula Vista")
    print("Del Mar")
    print("Escondido")
    print("Fallbrook")

    print(16)
    for i in range(4):
        print(0)
    for i in range(4):
        print(1)
    for i in range(4):
        print(2)
    for i in range(4):
        print(3)

    # print(0)
    # print(len(teams))
    # for i in range(len(teams)):
        # print(-1)

    """
    The point value of the first type of question, or 0 if the first slot is unused
    The point value of the second type of question, or 0 if the second slot is unused
    The point value of the third type of question, or 0 if the third slot is unused
    The point value of the fourth type of question, or 0 if the fourth slot is unused
    If packet names are used, then the number of packet names, otherwise 0
    If packet names are used, then each packet name in order. (This leaf node in our documentation represents as many lines as there are packet names specified, which might be no lines at all.)
    """

    print(15)
    print(10)
    print(-5)
    print(0)
    print(0)

    """
    The number of teams
    For each team according to its index, 1 if it is an exhibition team, otherwise 0. (This leaf node in our documentation represents as many lines as there are teams.)
    """
    print(len(teams))
    for i in range(len(teams)):
        print(0)


games = get_games_from_round(1)
for i in range(2, 10):
    games += get_games_from_round(i)

# games = get_games_from_round(8)
# games += get_games_from_round(9)

teams = extract_teams_from_games(games)

# generate_sqbs_file("CALISTO Online - Standard", games, teams)
