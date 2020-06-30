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

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
SHEET_CRED_FILE = 'sheets.googleapis.com-python-quickstart.json'
DRIVE_CRED_FILE = 'drive.json'
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = 'UCSD Scoresheets'


def get_gridRange(A1, i):
    col = A1[0]
    row = int(A1[1:])
    d = {i: string.ascii_uppercase.index(i) for i in string.ascii_uppercase}
    return {"sheetId": i, "startRowIndex": row - 1, "endRowIndex": row, "startColumnIndex": d[col], "endColumnIndex": d[col] + 1}


def get_rooms():
    d = OrderedDict()
    while True:
        inp = input("room number: ")
        if(len(inp) == 0):
            break
        else:
            d[inp] = ""
    return d


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


class ScoresheetGenerator:
    def __init__(self, *, checkboxes=False, tournament_name, scoresheet_id, aggregate_id, roster_id, room_names):
        self.tournament_name = tournament_name
        self.scoresheet_id = scoresheet_id
        self.aggregate_id = aggregate_id
        self.roster_id = roster_id
        self.room_names = room_names
        self.room_ids = dict()

        self.sheet_names = ["Round " + str(i + 1) for i in range(15)]
        self.A_PLAYERS = ["C3", "D3", "E3", "F3", "G3", "H3"]
        self.B_PLAYERS = ["M3", "N3", "O3", "P3", "Q3", "R3"]

        if checkboxes:
            self.team_a_range = "{}!C1:H3"
            self.team_b_range = "{}!O1:T3"
            self.indiv_a_range = "{}!C32:H36"
            self.indiv_b_range = "{}!O32:T36"

            self.TEAM_A = "C1"
            self.TEAM_B = "O1"
            self.TEAMS = "AB4"
            self.A_ROSTERS = "AC4"
            self.B_ROSTERS = "AD4"

            self.TEAM_VAL = "AB"
            self.TEAM_A_VAL = "AC"
            self.TEAM_B_VAL = "AD"

        else:
            self.team_a_range = "{}!C1:H3"
            self.team_b_range = "{}!M1:R3"
            self.indiv_a_range = "{}!C32:H36"
            self.indiv_b_range = "{}!M32:R36"

            self.TEAM_A = "C1"
            self.TEAM_B = "M1"
            self.TEAMS = "X4"
            self.A_ROSTERS = "Y4"
            self.B_ROSTERS = "Z4"

            self.TEAM_VAL = "X"
            self.TEAM_A_VAL = "Y"
            self.TEAM_B_VAL = "Z"

        self.left_col = ["=CONCAT(\"A BP: \",IMPORTRANGE(\"{}\",\"{}!I32\"))", "=CONCAT(\"B BP: \",IMPORTRANGE(\"{}\",\"{}!U32\"))",
                         "TUH", "15", "10", "-5", "Total", "=IMPORTRANGE(\"{}\",\"{}!AA1\")"]
        self.importrange_fstring = "={{IMPORTRANGE(\"{}\",\"{}\"),IMPORTRANGE(\"{}\",\"{}\")}}"

    def generate(self):
        self.create_scoresheets()
        self.populate_aggregate()
        self.populate_rooms()
        self.rosters()

    def create_scoresheets(self):
        # set up APIs
        driveService = discovery.build('drive', 'v3', credentials=get_credentials(DRIVE_CRED_FILE))

        credentials = get_credentials(DRIVE_CRED_FILE)
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build(
            'sheets', 'v4', credentials=credentials, discoveryServiceUrl=discoveryUrl)

        # create a new folder to move all sheets to
        file_metadata = {
            'name': self.tournament_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        file = driveService.files().create(body=file_metadata, fields='id').execute()
        folder_id = file.get('id')

        # create aggregate sheet, roster sheet, room sheets
        file_metadata = {"name": "Aggregate Scoresheets", "parents": [folder_id]}
        c = driveService.files().copy(fileId=self.aggregate_id, body=file_metadata).execute()
        self.aggregate_id = c["id"]  # update in place with ID's of copies

        file_metadata = {"name": "Rosters", "parents": [folder_id]}
        c = driveService.files().copy(fileId=self.roster_id, body=file_metadata).execute()
        self.roster_id = c["id"]

        for room in self.room_names:
            file_metadata = {"name": room, "parents": [folder_id]}
            c = driveService.files().copy(fileId=self.scoresheet_id, body=file_metadata).execute()
            self.room_ids[room] = c["id"]

        # print("Created room sheets")

    def populate_aggregate(self):
        for sheet_name in self.sheet_names:
            i = 1
            for room in self.room_ids:
                left_col_fmted = copy(left_col)
                left_col_fmted.insert(0, room)
                left_col_fmted[1] = left_col_fmted[1].format(self.room_ids[room], sheet_name)
                left_col_fmted[2] = left_col_fmted[2].format(self.room_ids[room], sheet_name)
                left_col_fmted[8] = left_col_fmted[8].format(self.room_ids[room], sheet_name)

                data = [{"range": sheet_name+"!A{}:A{}".format(i, i+9), "values": [left_col_fmted]},
                        {"range": sheet_name+"!B{}".format(i),
                         "values": [[importrange_fstring.format(self.room_ids[room], team_a_range.format(sheet_name), self.room_ids[room], team_b_range.format(sheet_name))]]},
                        {"range": sheet_name+"!B{}".format(i+3),
                         "values": [[importrange_fstring.format(self.room_ids[room], indiv_a_range.format(sheet_name), self.room_ids[room], indiv_b_range.format(sheet_name))]]}]

                data.append({"range": sheet_name + "!B{}".format(i+8),
                             "values": [["https://docs.google.com/spreadsheets/d/{}/edit".format(self.room_ids[room])]]})
                d = {}
                for j in data:
                    j["majorDimension"] = "COLUMNS"
                d["data"] = data
                d["valueInputOption"] = "USER_ENTERED"

                res = service.spreadsheets().values().batchUpdate(spreadsheetId=agg_id, body=d).execute()
                i += 10
            print("Finished: " + sheet_name)
        print("Finished aggregation")


    def populate_rooms(self):
        data = [{"range": "Rosters!A1", "values": [
            ["=IMPORTRANGE(\"{}\", \"Rosters!A:G\")".format(master_roster_id)]]}]

        for s in sheet_names:
            data.append({"range": "{}!{}".format(s, self.A_ROSTERS), "values": [
                        ["=TRANSPOSE(FILTER(Rosters!B:G, Rosters!A:A = {}))".format(self.TEAM_A)]]})
            data.append({"range": "{}!{}".format(s, self.B_ROSTERS), "values": [
                        ["=TRANSPOSE(FILTER(Rosters!B:G, Rosters!A:A = {}))".format(self.TEAM_B)]]})
            data.append({"range": "{}!{}".format(s, self.TEAMS),
                        "values": [["=ARRAYFORMULA(Rosters!A:A)"]]})

        d = {}
        for j in data:
            j["majorDimension"] = "COLUMNS"
            d["data"] = data
            d["valueInputOption"] = "USER_ENTERED"
            for i in self.room_ids:
                res = service.spreadsheets().values().batchUpdate(spreadsheetId=self.room_ids[i], body=d).execute()
            print(j)

        sheetIds = {}
        for i in self.room_ids:
            a = []
            b = service.spreadsheets().get(spreadsheetId=self.room_ids[i]).execute()
            sheetIds[i] = [j["properties"]["sheetId"] for j in b["sheets"]]


    def rosters(self):
        for i in self.room_ids:
            request = []
            k = 0

            for sheetname in sheet_names:
                for A in self.A_PLAYERS:
                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(A, sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        # { "userEnteredValue" : "=Y:Y" }
                                        {"userEnteredValue": "={}:{}".format(TEAM_A_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            } } }
                    request.append(dropdown_action)

                for B in self.B_PLAYERS:
                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(B, sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        # { "userEnteredValue" : "=Z:Z" }
                                        {"userEnteredValue": "={}:{}".format(TEAM_B_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            } } }
                    request.append(dropdown_action)

                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(self.TEAM_A, sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        # { "userEnteredValue" : "=X:X" }
                                        {"userEnteredValue": "={}:{}".format(TEAM_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            } } }
                    request.append(dropdown_action)

                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(self.TEAM_B, sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        # { "userEnteredValue" : "=X:X" }
                                        {"userEnteredValue": "={}:{}".format(TEAM_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            } } }
                    request.append(dropdown_action)
                    k += 1

            # print(request)
            batchUpdateRequest = {'requests': request}
            service.spreadsheets().batchUpdate(spreadsheetId=self.room_ids[i], body=batchUpdateRequest).execute()

            print("Finished Rosters")

