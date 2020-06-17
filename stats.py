from __future__ import print_function
import httplib2
import os
import pickle
import string
import json
import time

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

"""
# Constants for noncheckboxed sheets
RANGE_START = "C1"
RANGE_END = "S23"

NUM_PLAYERS = 6
B_COL_LEN = 1
T2_START = 10
"""

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

def read_scoresheets():
    for round_num in range(1, 12):
        """
        for scoresheet_id in [ "1fW2a_7IhQoOzb4Pbq4Cck8TWEd3KST2zYlJOM34UFsw",  # AM
                            "1cm_X3R9kyX9NSzXc_h6kwN8K-rFJ4A9ejlzQvNLHTfs",  # CA
                            "1KWxsh9SG3hVv9oPANMgBaVu2paCaXZJ9mvvLlmmgBxM",  # EL
                            "1iJdRBE9FsstO4PIFL9Isz2g_G888lujytutxC-2IQHE",  # EU
                            "1AzvmJUTjCKCtcFZdPPUypMae-o2dFtCNd6W3bzhDNkQ",  # GA
                            "1tUU0c3PtXX2awuRSUBmvxHsrsdDZbBEHuBRDhnFrD-w",  # HI
                            "1ifT3Ry5bEZqxydr--mBpFlNk3JKncLFQ9_WRScDLIjA",  # IO
                            "1aWiCum5G4tEBY8UY9HRYJh2zc4-zDFrbgYP3Pz-HF_Y"]: # TH
        """
        for scoresheet_id in [ "1BjMO6lGSM3wCcLFcUsd57s908ktAxfYUCA8YYGm8AaA", # AN
                               "1Oq9nrm41jsr0IO2jy9Tl3OxRgzPmVTjNCC1dV3EvnGo", # AT
                               "1vQ6tZiqSyT-69QEKfR9wL5y_Z7lWBrNH_7k-oQQzLaM", # HE
                               "1f61R63mu1tAKpOmoWf9w9HLzAUCCpFin44QWAHfw6Yw", # HI
                               "10vyI4LZlhOEqpW5yJSUAMKtRYzj38czIkJkri44dT5Q", # LO
                               "1EutvpQxciHIwLps-CaPHcmVS9ZXfsvfZPAsA8hN1d6E", # OR
                               "1bLSaXbbKtxAGirTRuf-waexc4uifg-NBHeCiGjeUL9I", # OU
                               "1aD3Ft0T0DLMw0x5-0FmiLhjgyC9BX9AEeB21nFdyboA"]: # PR

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

    with open("stan_stats", "w") as f:
        json.dump({"tossups": tossups, "bonuses": bonuses, "teams": team_names}, f)

def compute_p_n_counts(data):
    stats = {(i, j) : 0 for i in range(17) for j in range(17)}

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
            print(stats[(i,j)], end=" ")
        print()

def compute_conversion(data):
    for packet in range(1, 11):
        for tossup in range(20):
            tu_stats = {15: 0, 10: 0, -5: 0}
            for team in data["teams"]:
                if str(packet) not in data["tossups"][team]:
                    continue
                points = data["tossups"][team][str(packet)][tossup]
                if points in tu_stats:
                    tu_stats[points] += 1
            print("{}/{}/{}".format(tu_stats[15], tu_stats[10], tu_stats[-5]), end="\t")
        print("")

# read_scoresheets()

# with open("stan_stats", "r") as f:
s = open("stan_stats", "r")
s_data = json.load(s)
c = open("comp_stats", "r")
c_data = json.load(c)

merged = {"tossups": {**c_data["tossups"], **s_data["tossups"]},
          "bonuses": {**c_data["bonuses"], **s_data["bonuses"]},
          "teams"  : c_data["teams"] + s_data["teams"]}

compute_p_n_counts(merged)
