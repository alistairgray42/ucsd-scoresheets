from __future__ import print_function
import os
import pickle
import json
import time

from apiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

checkboxed = True

##############################################################################

# Constants for checkboxed sheets
if checkboxed:
    RANGE_START = "C1"
    RANGE_END = "W23"

    NUM_PLAYERS = 6
    B_COL_LEN = 3
    T2_START = 12

else:
# Constants for noncheckboxed sheets
    RANGE_START = "C1"
    RANGE_END = "S23"

    NUM_PLAYERS = 6
    B_COL_LEN = 1
    T2_START = 10

T1_B_START = NUM_PLAYERS
T2_B_START = T2_START + NUM_PLAYERS

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
discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
service = discovery.build('sheets', 'v4', credentials=credentials, discoveryServiceUrl=discoveryUrl)
sheets = service.spreadsheets()

tossups = dict()
# {"Team name" : {1: [10, 15, 0, ...], ...}, ...}
bonuses = dict()
# {"Team name" : {1: [2, 7, -1, ...], ...}, ...}

# Tossups:
# 15
# 10
# -5
# 0: Opponent converted
# -1: Did not hear
# -2: Dead

# Bonuses:
# 0:  000
# 1:  001
# 2:  010
# 3:  011
# 4:  100
# 5:  101
# 6:  110
# 7:  111
# -1: Did not hear


def assign_tu(data):
    for val in data:
        if val != '':
            return int(val)
    return 0


def assign_b(data):
    if len(data) == 1:
        return int(data[0])

    ret = 0
    if data[0] == 'TRUE':
        ret += 4
    if data[1] == 'TRUE':
        ret += 2
    if data[2] == 'TRUE':
        ret += 1
    return ret


def read_scoresheets(round_min, round_max, scoresheet_ids):
    for round_num in range(1, 12):
        for scoresheet_id in scoresheet_ids:

            result = sheets.values().get(spreadsheetId=scoresheet_id,
                                         range=f"Round {round_num}!{RANGE_START}:{RANGE_END}").execute()
            values = result.get('values', [])
            team_1, team_2 = values[0][0], values[0][-1]

            t1_tus = []
            t2_tus = []
            t1_bs = []
            t2_bs = []

            for row_num in range(3, len(values)):
                t1_tu = assign_tu(values[row_num][:NUM_PLAYERS])
                t2_tu = assign_tu(
                    values[row_num][T2_START: T2_START+NUM_PLAYERS])

                if t1_tu == 0 and t2_tu <= 0:
                    t1_tu = -2

                if t2_tu == 0 and t1_tu <= 0:
                    t2_tu = -2

                t1_b = assign_b(
                    values[row_num][T1_B_START: T1_B_START+B_COL_LEN]) if t1_tu > 0 else -1
                t2_b = assign_b(
                    values[row_num][T2_B_START: T2_B_START+B_COL_LEN]) if t2_tu > 0 else -1

                t1_tus.append(t1_tu)
                t2_tus.append(t2_tu)

                # track bonuses of dead tossups correctly
                # if t1_tu > 0 or t2_tu > 0:
                    # t1_bs.append(t1_b)
                    # t2_bs.append(t2_b)
                t1_bs.append(t1_b)
                t2_bs.append(t2_b)

            if team_1 not in tossups:
                tossups[team_1] = dict()
                bonuses[team_1] = dict()

            if team_2 not in tossups:
                tossups[team_2] = dict()
                bonuses[team_2] = dict()

            tossups[team_1][round_num] = t1_tus
            bonuses[team_1][round_num] = t1_bs
            tossups[team_2][round_num] = t2_tus
            bonuses[team_2][round_num] = t2_bs

            print("Round {}: {}".format(round_num, scoresheet_id))
            time.sleep(1)
        time.sleep(2)

    # delete placeholder team names
    if "Team A" in tossups:
        del tossups["Team A"]
        del tossups["Team B"]
        del bonuses["Team A"]
        del bonuses["Team B"]

    max_round_num = 0
    for team in tossups.values():
        if max(team.keys()) > max_round_num:
            max_round_num = max(team.keys())

    team_names = list(tossups.keys())

    data = {"tossups": tossups, "bonuses": bonuses, "teams": team_names}
    with open("stats", "w") as f:
        json.dump(data, f)
    return read_from_file(data)


def compute_p_n_counts(data):
    stats = {(i, j): 0 for i in range(17) for j in range(17)}

    for packet in range(1, 10):
        for tossup in range(20):
            powers = 0
            negs = 0
            for team in data["teams"]:
                if str(packet) not in data["tossups"][team]:
                    continue
                value = data["tossups"][team][str(packet)][tossup]
                if value == 15:
                    powers += 1
                if value == -5:
                    negs += 1
            stats[(powers, negs)] += 1

    for i in range(17):
        for j in range(17):
            print(stats[(i, j)], end=" ")
        print()

def compute_tossup_conversion(data, max_round):
    for q_num in range(1, 21):
        print(q_num, end=",,,,,")
    print("")

    for _ in range(1, 21):
        print("15,10,-5,,,", end="")
    print("")

    for packet in range(1, max_round):
        for tossup in range(20):
            tu_stats = {15: 0, 10: 0, -5: 0}
            for team in data["teams"]:
                if str(packet) not in data["tossups"][team]:
                    continue
                points = data["tossups"][team][str(packet)][tossup]
                if points in tu_stats:
                    tu_stats[points] += 1
            print("{},{},{},,,".format(tu_stats[15], tu_stats[10], tu_stats[-5]), end="")
        print("")


def compute_bonus_conversion(data, max_round):
    for q_num in range(1, 21):
        print(q_num, end=",,,,,")
    print("")

    for _ in range(1, 21):
        print("1,2,3,,,", end="")
    print("")

    overall_stats_string = ""
    for packet in range(1, max_round):
        for bonus in range(20):
            b_stats = {1: 0, 2: 0, 3: 0, 0: 0, 10: 0, 20: 0, 30: 0}
            for team in data["teams"]:
                if str(packet) not in data["bonuses"][team]:
                    continue
                if bonus >= len(data["bonuses"][team][str(packet)]):
                    continue
                points = data["bonuses"][team][str(packet)][bonus]
                if points >= 0:
                    parts = 0
                    if points >= 4:
                        b_stats[1] += 1
                        parts += 1
                    if points == 2 or points == 3 or points == 6 or points == 7:
                        b_stats[2] += 1
                        parts += 1
                    if points % 2 == 1:
                        b_stats[3] += 1
                        parts += 1

                    b_stats[parts * 10] += 1

            print("{},{},{},,,".format(b_stats[1], b_stats[2], b_stats[3]), end="")
            overall_stats_string += "{},{},{},{},,".format(b_stats[0], b_stats[10], b_stats[20], b_stats[30])
        print("")
        overall_stats_string += "\n"
    print("")

    for q_num in range(1, 21):
        print(q_num, end=",,,,,")
    print("")

    for _ in range(1, 21):
        print("0,10,20,30,,", end="")

    print("")

    print(overall_stats_string)

def compute_conversion(data, max_round):
    compute_tossup_conversion(data, max_round)
    compute_bonus_conversion(data, max_round)

def read_from_file(filename):
    return json.load(open(filename, "r"))

def combine_two(filename_1, filename_2):
    data_1 = json.load(open(filename_1, "r"))
    data_2 = json.load(open(filename_2, "r"))

    merged = {"tossups": {**data_1["tossups"], **data_2["tossups"]},
            "bonuses": {**data_1["bonuses"], **data_2["bonuses"]},
            "teams": data_1["teams"] + data_2["teams"]}
    print(merged)
