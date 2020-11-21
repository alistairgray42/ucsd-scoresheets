from __future__ import print_function
import httplib2
import os
import pickle
import string
import sys
import json

from collections import OrderedDict

from apiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from copy import copy

from utils import send_completion_email, generate_filename

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
    def __init__(self, *, checkboxes=False, tournament_name, email, room_names):
        self.tournament_name = tournament_name
        self.email = email
        self.room_names = room_names
        self.room_ids = dict()

        self.sheet_names = ["Round " + str(i + 1) for i in range(15)]
        self.A_PLAYERS = ["C3", "D3", "E3", "F3", "G3", "H3"]
        self.B_PLAYERS = ["M3", "N3", "O3", "P3", "Q3", "R3"]

        # TEMPORARY! Templates!
        self.roster_id = "1k8H0kUeE3gwNpZjyIq8cUbEatwNzA-NNGWdS8YdiFeU"
        self.aggregate_id = "1uvBPrEUoFNadWTIzIYfjtCwo328vPangAw_AXjGtOg4"

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

            self.left_col = ["=CONCAT(\"A BP: \",IMPORTRANGE(\"{}\",\"{}!I32\"))",
                             "=CONCAT(\"B BP: \",IMPORTRANGE(\"{}\",\"{}!U32\"))", "TUH", "15",
                             "10", "-5", "Total", "=IMPORTRANGE(\"{}\",\"{}!AA1\")"]

            # TEMPORARY! Template!
            self.scoresheet_id = "1_XuTrn4cmxE1IxGzOkc8l-VqMaE-vn1eWzwv8rs1lyE"

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

            self.left_col = ["=CONCAT(\"A BP: \",IMPORTRANGE(\"{}\",\"{}!I32\"))",
                             "=CONCAT(\"B BP: \",IMPORTRANGE(\"{}\",\"{}!S32\"))", "TUH", "15",
                             "10", "-5", "Total", "=IMPORTRANGE(\"{}\",\"{}!W1\")"]

            # TEMPORARY! Template!
            self.scoresheet_id = "1pv0Z5kvxfij0KCRAQG9lOxfaax-HftmGnDxQn59SDPY"

        self.documentation_id = "1rucjWOWmCq7c8fmqniZ5NCKrHQOCfOkW86TgDbMQkYk"

        self.importrange_fstring = "={{IMPORTRANGE(\"{}\",\"{}\"),IMPORTRANGE(\"{}\",\"{}\")}}"

    def create_scoresheets(self):
        # set up APIs
        driveService = discovery.build('drive', 'v3', credentials=get_credentials(DRIVE_CRED_FILE))
        self.driveService = driveService

        credentials = get_credentials(DRIVE_CRED_FILE)
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        self.service = discovery.build('sheets', 'v4', credentials=credentials, discoveryServiceUrl=discoveryUrl)

        # create a new folder to move all sheets to
        file_metadata = {
            'name': self.tournament_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        file = driveService.files().create(body=file_metadata, fields='id').execute()
        self.folder_id = file.get('id')

        # create aggregate sheet, roster sheet, room sheets
        file_metadata = {"name": "Aggregate Scoresheets", "parents": [self.folder_id]}
        c = driveService.files().copy(fileId=self.aggregate_id, body=file_metadata).execute()
        self.aggregate_id = c["id"]  # update ID's in place with ID's of copies

        file_metadata = {"name": "Rosters", "parents": [self.folder_id]}
        c = driveService.files().copy(fileId=self.roster_id, body=file_metadata).execute()
        self.roster_id = c["id"]

        for room in self.room_names:
            file_metadata = {"name": room, "parents": [self.folder_id]}
            c = driveService.files().copy(fileId=self.scoresheet_id,
                                          body=file_metadata).execute()
            self.room_ids[room] = c["id"]

        # create documentation doc
        file_metadata = {"name": "Using UCSD Scoresheets", "parents": [self.folder_id]}
        c = driveService.files().copy(fileId=self.documentation_id, body=file_metadata).execute()

    def populate_aggregate(self):
        data = []

        for sheet_name in self.sheet_names:
            i = 1
            for room in self.room_ids:
                left_col_fmted = copy(self.left_col)
                left_col_fmted.insert(0, room)
                left_col_fmted[1] = left_col_fmted[1].format(self.room_ids[room], sheet_name)
                left_col_fmted[2] = left_col_fmted[2].format(self.room_ids[room], sheet_name)
                left_col_fmted[8] = left_col_fmted[8].format(self.room_ids[room], sheet_name)

                data.append({"range": f"{sheet_name}!A{i}:A{i + 9}", "values": [left_col_fmted]})

                data.append({"range": f"{sheet_name}!B{i}",
                             "values": [[self.importrange_fstring.format(self.room_ids[room], self.team_a_range.format(sheet_name),
                                                                         self.room_ids[room], self.team_b_range.format(sheet_name))]]})

                data.append({"range": f"{sheet_name}!B{i + 3}",
                             "values": [[self.importrange_fstring.format(self.room_ids[room], self.indiv_a_range.format(sheet_name),
                                                                         self.room_ids[room], self.indiv_b_range.format(sheet_name))]]})

                data.append({"range": f"{sheet_name}!B{i + 8}",
                             "values": [["https://docs.google.com/spreadsheets/d/{}/edit".format(self.room_ids[room])]]})

                i += 10

        d = {}
        for j in data:
            j["majorDimension"] = "COLUMNS"
        d["data"] = data
        d["valueInputOption"] = "USER_ENTERED"

        res = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.aggregate_id, body=d).execute()

    def populate_rooms(self):
        data = [{"range": "Rosters!A1", "values": [["=IMPORTRANGE(\"{}\", \"Rosters!A2:G\")".format(self.roster_id)]]}]

        for s in self.sheet_names:
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
            res = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.room_ids[i], body=d).execute()

        self.sheetIds = {}
        for i in self.room_ids:
            b = self.service.spreadsheets().get(spreadsheetId=self.room_ids[i]).execute()
            self.sheetIds[i] = [j["properties"]["sheetId"] for j in b["sheets"]]

    def rosters(self):
        for i in self.room_ids:
            request = []
            k = 0

            for sheetname in self.sheet_names:
                for A in self.A_PLAYERS:
                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(A, self.sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        {"userEnteredValue": "={}:{}".format(
                                            self.TEAM_A_VAL, self.TEAM_A_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            }}}
                    request.append(dropdown_action)

                for B in self.B_PLAYERS:
                    dropdown_action = {
                        'setDataValidation': {
                            'range': get_gridRange(B, self.sheetIds[i][k]),
                            'rule': {
                                'condition': {
                                    'type': 'ONE_OF_RANGE',
                                    'values': [
                                        {"userEnteredValue": "={}:{}".format(
                                            self.TEAM_B_VAL, self.TEAM_B_VAL)}
                                    ],
                                },
                                'inputMessage': 'Choose one from dropdown',
                                'showCustomUi': True
                            }}}
                    request.append(dropdown_action)

                dropdown_action = {
                    'setDataValidation': {
                        'range': get_gridRange(self.TEAM_A, self.sheetIds[i][k]),
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_RANGE',
                                'values': [
                                    {"userEnteredValue": "={}:{}".format(
                                        self.TEAM_VAL, self.TEAM_VAL)}
                                ],
                            },
                            'inputMessage': 'Choose one from dropdown',
                            'showCustomUi': True
                        }}}
                request.append(dropdown_action)

                dropdown_action = {
                    'setDataValidation': {
                        'range': get_gridRange(self.TEAM_B, self.sheetIds[i][k]),
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_RANGE',
                                'values': [
                                    {"userEnteredValue": "={}:{}".format(
                                        self.TEAM_VAL, self.TEAM_VAL)}
                                ],
                            },
                            'inputMessage': 'Choose one from dropdown',
                            'showCustomUi': True
                        }}}
                request.append(dropdown_action)

                k += 1

            batchUpdateRequest = {'requests': request}
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.room_ids[i], body=batchUpdateRequest).execute()

    def generate(self):
        self.create_scoresheets()
        self.populate_aggregate()
        self.populate_rooms()
        self.rosters()

    def share_with_recipient(self):
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': self.email
        }

        SHARE_MESSAGE = """Thanks for using UCSD Scoresheets!

        This is the folder containing your scoresheets; make sure to go into each sheet and connect them as necessary. (Check the documentation in the folder if you don't know how to do this.)
        """

        self.driveService.permissions().create(fileId=self.folder_id, body=permission, emailMessage=SHARE_MESSAGE).execute()

    # TODO: use a proper database for all this
    def write_config(self):
        with open(os.path.join("sqbs_configs", generate_filename(self.email, ".json")), 'w') as f:
            json.dump({"agg_id": self.aggregate_id,
                       "roster_id": self.roster_id,
                       "last_run": 0}, f)


def generate_from_file(filename):
    with open(filename, 'r') as f:
        j = json.load(f)

        sg = ScoresheetGenerator(
            checkboxes=("bonus_tracking" in j and j["bonus_tracking"] == "on"),
            tournament_name=j["tourney_name"],
            email=j["email"],
            room_names=j["rooms"])

        sg.generate()
        sg.share_with_recipient()
        sg.write_config()
