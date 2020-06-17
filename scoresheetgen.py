from __future__ import print_function
import httplib2
import os
import pickle
import string

from collections import OrderedDict

from apiclient import discovery
# from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from copy import copy
from time import sleep

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
SHEET_CRED_FILE = 'sheets.googleapis.com-python-quickstart.json'
DRIVE_CRED_FILE = 'drive.json'
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'
sheet_names = ["Round 1", "Round 2", "Round 3", "Round 4", "Round 5", "Round 6", "Round 7",
               "Round 8", "Round 9", "Round 10", "Round 11" , "Round 12", "Round 13"]
            #, "Round 14" , "Round 15", "Round 16", "Finals/Emergency", "Finals 2/Emergency"]
left_col = ["=CONCAT(\"A BP: \",IMPORTRANGE(\"{}\",\"{}!I32\"))", "=CONCAT(\"B BP: \",IMPORTRANGE(\"{}\",\"{}!U32\"))", "TUH", "15", "10", "-5", "Total", "=IMPORTRANGE(\"{}\",\"{}!AA1\")"]
team_a_range = "{}!C1:H3"
# team_b_range = "{}!M1:R3"
team_b_range = "{}!O1:T3"
indiv_a_range = "{}!C32:H36"
# indiv_b_range = "{}!M32:R36"
indiv_b_range = "{}!O32:T36"
importrange_fstring = "={{IMPORTRANGE(\"{}\",\"{}\"),IMPORTRANGE(\"{}\",\"{}\")}}"

def get_gridRange(A1, i):
    col = A1[0]
    row = int(A1[1:])
    d = {i:string.ascii_uppercase.index(i) for i in string.ascii_uppercase}
    return {"sheetId" : i, "startRowIndex" : row -1, "endRowIndex" : row, "startColumnIndex" : d[col], "endColumnIndex": d[col] + 1}

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
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(filename, 'wb') as token:
            pickle.dump(creds, token)
    return creds

driveService = discovery.build('drive', 'v3', credentials=get_credentials(DRIVE_CRED_FILE))

master_scoresheet_id = input("Master scoresheet id: ")
master_agg_id = input("Master aggregate id: ")
master_roster_id = input("Master roster id: ")

rooms = get_rooms()
credentials = get_credentials(DRIVE_CRED_FILE)
discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                'version=v4')
service = discovery.build('sheets', 'v4', credentials=credentials, discoveryServiceUrl=discoveryUrl)

c = driveService.files().copy(fileId=master_agg_id, body={"name": "Aggregate Scoresheets"}).execute()
agg_id = c["id"]

for room in rooms:
    c = driveService.files().copy(fileId=master_scoresheet_id, body={"name": room}).execute()
    rooms[room] = c["id"]

print("Created room sheets")

k = 0
for name in sheet_names:
    i = 1
    for room in rooms:
        left_col_fmted = copy(left_col)
        left_col_fmted.insert(0, room)
        left_col_fmted[1] = left_col_fmted[1].format(rooms[room], name)
        left_col_fmted[2] = left_col_fmted[2].format(rooms[room], name)
        left_col_fmted[8] = left_col_fmted[8].format(rooms[room], name)
        data = [{"range": name+"!A{}:A{}".format(i, i+9), "values":[left_col_fmted]},
                {"range": name+"!B{}".format(i), "values":[[importrange_fstring.format(rooms[room], team_a_range.format(name), rooms[room], team_b_range.format(name))]]},
                {"range": name+"!B{}".format(i+3), "values":[[importrange_fstring.format(rooms[room], indiv_a_range.format(name), rooms[room], indiv_b_range.format(name))]]}]
        data.append({"range": name + "!B{}".format(i+8),"values":[["https://docs.google.com/spreadsheets/d/{}/edit".format(rooms[room])]]})
        d = {}
        for j in data:
            j["majorDimension"] = "COLUMNS"
        d["data"] = data
        d["valueInputOption"] = "USER_ENTERED"
        res = service.spreadsheets().values().batchUpdate(spreadsheetId=agg_id, body=d).execute()
        sleep(1)
        i += 10
    print("Finished: "  + name)
print("Finished aggregation")

TEAM_A = "C1"
TEAM_B = "O1"
# TEAM_B = "M1"
# TEAMS = "X4"
# A_ROSTERS = "Y4"
# B_ROSTERS = "Z4"
TEAMS = "AB4"
A_ROSTERS = "AC4"
B_ROSTERS = "AD4"

A_PLAYERS = ["C3","D3","E3","F3","G3","H3"]
B_PLAYERS = ["M3","N3","O3","P3","Q3","R3"]

data = [{"range": "Rosters!A1", "values":[["=IMPORTRANGE(\"{}\", \"Rosters!A:G\")".format(master_roster_id)]]}]
for s in sheet_names:
    data.append({"range":"{}!{}".format(s, A_ROSTERS), "values":[["=TRANSPOSE(FILTER(Rosters!B:G, Rosters!A:A = {}))".format(TEAM_A)]]})
    data.append({"range":"{}!{}".format(s, B_ROSTERS), "values":[["=TRANSPOSE(FILTER(Rosters!B:G, Rosters!A:A = {}))".format(TEAM_B)]]})
    data.append({"range":"{}!{}".format(s, TEAMS), "values":[["=ARRAYFORMULA(Rosters!A:A)"]]})

d = {}
for j in data:
    j["majorDimension"] = "COLUMNS"
    d["data"] = data
    d["valueInputOption"] = "USER_ENTERED"
    for i in rooms:
        res = service.spreadsheets().values().batchUpdate(spreadsheetId=rooms[i], body=d).execute()
        sleep(1)
    print(j)

sleep(5)

sheetIds = {}
for i in rooms:
    a = []
    b = service.spreadsheets().get(spreadsheetId=rooms[i]).execute()
    sleep(1)
    # for j in b["sheets"]:
        # a.append(j["properties"]["sheetId"])
    # sheetIds[i] = a
    sheetIds[i] = [j["properties"]["sheetId"] for j in b["sheets"]]


def j():
    for i in rooms:
        request = []
        k = 0
        for sheetname in sheet_names:
            for A in A_PLAYERS:
                dropdown_action = {
                    'setDataValidation':{
                        'range':
                        get_gridRange(A, sheetIds[i][k])
                        ,
                        'rule':{
                            'condition':{
                                'type':'ONE_OF_RANGE',
                                'values': [
                                    # { "userEnteredValue" : "=Y:Y" }
                                    { "userEnteredValue" : "=AC:AC" }
                                ],
                            },
                            'inputMessage' : 'Choose one from dropdown',
                            'showCustomUi': True
                        }

                    }
                }
                request.append(dropdown_action)
            for B in B_PLAYERS:
                dropdown_action = {
                    'setDataValidation':{
                        'range':
                        get_gridRange(B, sheetIds[i][k])
                        ,
                        'rule':{
                            'condition':{
                                'type':'ONE_OF_RANGE',
                                'values': [
                                    # { "userEnteredValue" : "=Z:Z" }
                                    { "userEnteredValue" : "=AD:AD" }
                                ],
                            },
                            'inputMessage' : 'Choose one from dropdown',
                            'showCustomUi': True
                        }

                    }
                }
                request.append(dropdown_action)
                dropdown_action = {
                    'setDataValidation':{
                        'range':
                        get_gridRange(TEAM_A, sheetIds[i][k])
                        ,
                        'rule':{
                            'condition':{
                                'type':'ONE_OF_RANGE',
                                'values': [
                                    # { "userEnteredValue" : "=X:X" }
                                    { "userEnteredValue" : "=AB:AB" }
                                ],
                            },
                            'inputMessage' : 'Choose one from dropdown',
                            'showCustomUi': True
                        }

                    }
                }
                request.append(dropdown_action)
                dropdown_action = {
                    'setDataValidation':{
                        'range':
                        get_gridRange(TEAM_B, sheetIds[i][k])
                        ,
                        'rule':{
                            'condition':{
                                'type':'ONE_OF_RANGE',
                                'values': [
                                    # { "userEnteredValue" : "=X:X" }
                                    { "userEnteredValue" : "=AB:AB" }
                                ],
                            },
                            'inputMessage' : 'Choose one from dropdown',
                            'showCustomUi': True
                        }

                    }
                }
                request.append(dropdown_action)
                k+=1

        #print(request)
        batchUpdateRequest = {'requests': request}
        service.spreadsheets().batchUpdate(spreadsheetId = rooms[i], body = batchUpdateRequest).execute()


j()
print("Finished Rosters")
"""
for i in rooms:
    a = service.spreadsheets().sheets().copyTo(spreadsheetId=master_roster_id, sheetId="0", body={"destinationSpreadsheetId": rooms[i]}).execute()
    """

