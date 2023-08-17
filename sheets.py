from __future__ import print_function

import os.path
import datetime as dt
import time
import nest

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SAMPLE_SPREADSHEET_ID = '1VLHc3QEg9BUe7GMnXYRKa-F_UJeMZB-5E4-51Afw5_8'
SAMPLE_RANGE_NAME = 'summer_home'


def get_creds():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def read_sheet(creds,range_name):
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return
        
        return values

    except HttpError as err:
        print(err)



def main():

    creds = get_creds()
    current_date_time = round(time.time())
    current_date=time.strftime('%Y-%m-%d')
    
# ************* Process the master sheet details ***************
    values=read_sheet(creds,"MASTER")

    for row in values:
        if row[0]=="ENABLED":
            if row[1]!="1":
                exit()
        elif row[0]=="MANUAL_OVERRIDE_STATE":
            if row[1]=="OFF":
                #switch_heating_off()
                print("Switch Heating OFF")
                exit()
            elif row[1]=="HEAT":
                #switch_heating_on()
                print("Switch Heating ON")
                exit()
        elif row[0]=="CURRENT_SCHEDULE":
            current_schedule=row[1]
            #print(f"Current Schedule is {current_schedule}")

# ************* Get the current schedule sheet details ***************
    values=read_sheet(creds,current_schedule)

    on_times = []
    off_times = []
    for row in values:
        if row[0] != "TIME_ON":
            on_times.append(int(time.mktime(time.strptime(current_date+" "+row[0],"%Y-%m-%d %H:%M"))))
            off_times.append(int(time.mktime(time.strptime(current_date+" "+row[1],"%Y-%m-%d %H:%M"))))

    action_times = {}
    for on in on_times:
        if (on > current_date_time - 600) and (on <= current_date_time):
            action_times[on] = "HEAT"

    for off in off_times:
        if (off > current_date_time - 600) and (off <= current_date_time):
            action_times[off] = "OFF"

    #print(action_times)

    max_action_time = 0
    max_action = "NONE"
    for k,v in action_times.items():
        #print(f"Key : {k}, Value : {v}")
        if k > max_action_time:
            max_action_time = k
            max_action_time_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(max_action_time))
            max_action = v

    if max_action_time > 0:
        print(f"SWITCH {max_action}, scheduled time was {max_action_time_t} ({max_action_time}) from {current_schedule}")
        nest.set_nest_status(max_action,current_schedule,max_action_time_t)
    else:
        print("Nothing to do right now")




if __name__ == '__main__':
    main()