from __future__ import print_function
import httplib2
import os
import pickle
import string

from collections import OrderedDict

from apiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from copy import copy
from time import sleep

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
# -1: Did not convert after opponent neg

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
    ret = 0
    if data[0] == 'TRUE':
        ret += 4
    if data[1] == 'TRUE':
        ret += 2
    if data[2] == 'TRUE':
        ret += 1
    return ret

for round_num in (1, 2, 3):
    for scoresheet_id in ["1gybKKlNuxY53dIpABV26pPS1je2zCJrYd9Xxb3P_SCY"]:
        result = sheets.values().get(spreadsheetId=scoresheet_id,
                                     range=f"Round {round_num}!C1:W23").execute()
        values = result.get('values', [])
        team_1, team_2 = values[0][0], values[0][-1]

        t1_tus = []
        t2_tus = []
        t1_bs = []
        t2_bs = []

        for row_num in range(3, len(values)):
            t1_tu = assign_tu(values[row_num][:6])
            t2_tu = assign_tu(values[row_num][12:18])

            if t1_tu == 0 and t2_tu == -5:
                t1_tu = -1

            if t2_tu == 0 and t1_tu == -5:
                t2_tu = -1

            t1_b = assign_b(values[row_num][6:9]) if t1_tu > 0 else -1
            t2_b = assign_b(values[row_num][18:21]) if t2_tu > 0 else -1

            t1_tus.append(t1_tu)
            t2_tus.append(t2_tu)
            t1_bs.append(t1_b)
            t2_bs.append(t2_b)

        if team_1 not in tossups:
            tossups[team_1] = dict()
            bonuses[team_1] = dict()

        if team_2 not in bonuses:
            tossups[team_2] = dict()
            bonuses[team_2] = dict()

        tossups[team_1][round_num] = t1_tus
        bonuses[team_1][round_num] = t1_bs
        tossups[team_2][round_num] = t2_tus
        bonuses[team_2][round_num] = t2_bs

