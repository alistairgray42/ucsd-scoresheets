from __future__ import print_function
import httplib2
import os
import pickle
import string

import numpy as np

from apiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from copy import copy
from time import sleep

# Constants for checkboxed sheets
RANGE_START = "C1"
RANGE_END = "W23"

NUM_PLAYERS = 6
B_COL_LEN = 3
T2_START = 12

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
discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                'version=v4')

service = discovery.build('sheets', 'v4', credentials=credentials,
                          discoveryServiceUrl=discoveryUrl)

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

for round_num in (1, 2, 3):
    # for scoresheet_id in ["1gybKKlNuxY53dIpABV26pPS1je2zCJrYd9Xxb3P_SCY"]:
    for scoresheet_id in ["1qApfWqcmTYfyJor9F9rdFZYzAta_yeCeVB1iRkNispg",
                          "1NlT5-i21IWUTlTfNyhPzks5hA79I1oyBe3cARD8I4Go",
                          "18i1tHZ_apRm9JUyDxb0lQzbX_8fl0ED2f4yrdUh813k",
                          "1MeAlXLotLaLF7JCY6uQCtCnddEqPPW_Zs2rfbrRfjoA",
                          "17sQtdq0FfHlRuShYGTxJ8WzPsIWOCX4em-iRXJTau0I",
                          "10qh1x0XtG8NrQ_ZE6S3rNVtmXulE80DattBkkku22qM",
                          "1lFz3-4X-4FNw0stQaobsg0r6TQ13mvIFzwoyh4omz10",
                          "1uMJ-IsuOKmVfLNDgCZu45_8tQd1xXEzsj9cKC14Fa60"]:
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
            t2_tu = assign_tu(values[row_num][T2_START : T2_START+NUM_PLAYERS])

            if t1_tu == 0 and t2_tu <= 0:
                t1_tu = -2

            if t2_tu == 0 and t1_tu <= 0:
                t2_tu = -2

            t1_b = assign_b(values[row_num][T1_B_START : T1_B_START+B_COL_LEN]) if t1_tu > 0 else -1
            t2_b = assign_b(values[row_num][T2_B_START : T2_B_START+B_COL_LEN]) if t2_tu > 0 else -1

            t1_tus.append(t1_tu)
            t2_tus.append(t2_tu)

            # track bonuses of dead tossups correctly
            if t1_tu > 0 or t2_tu > 0:
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

num_teams = len(tossups)

np_tossups = np.full((num_teams, max_round_num, 20), -1)
np_bonuses = np.full((num_teams, max_round_num, 20), -1)

team_names = list(tossups.keys())

for team_number, team_data in enumerate(tossups.values()):
    for round_num, tossup_data in team_data.items():
        np_tossups[team_number][round_num - 1][:len(tossup_data)] = tossup_data

for team_number, team_data in enumerate(bonuses.values()):
    for round_num, bonus_data in team_data.items():
        np_bonuses[team_number][round_num - 1][:len(bonus_data)] = bonus_data

