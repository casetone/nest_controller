from __future__ import print_function

import os.path
from pprint import pprint

import datetime as dt
import time

from nest import Nest
from nest import Logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SAMPLE_SPREADSHEET_ID = "1VLHc3QEg9BUe7GMnXYRKa-F_UJeMZB-5E4-51Afw5_8"
SAMPLE_RANGE_NAME = "summer_home"


def get_creds():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    nest_path = os.getenv("NEST_PATH")

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(nest_path + "/token.json"):
        creds = Credentials.from_authorized_user_file(nest_path + "/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(nest_path + "/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(nest_path + "/token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def read_sheet(creds, range_name,logger):
    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=range_name)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            logger.write_splunk_log("info", "No data found.")
            return

        return values

    except HttpError as err:
        log_text = "HTTP ERROR : " + str(err)
        logger.write_splunk_log("info", log_text)
        exit


def main():

    logger = Logger()
    nest = Nest(logger)

    creds = get_creds()
    current_date_time = round(time.time())
    current_date = time.strftime("%Y-%m-%d")
    current_day = int(time.strftime("%w"))

    # ************* Process the master sheet details ***************
    values = read_sheet(creds, "MASTER",logger)

    for row in values:
        if row[0] == "ENABLED":
            if row[1] != "1":
                log_text = "NOT ENABLED - doing no work"
                logger.write_splunk_log("info", log_text)
                exit()
        elif row[0] == "MANUAL_OVERRIDE_STATE":
            if row[1] == "OFF":
                log_text = "MANUAL OVERRIDE OFF"
                logger.write_splunk_log("info", log_text)
                nest.get_nest_status()
                nest.set_nest_status("OFF", "OVERRIDE", "NONE")
                exit()
            elif row[1] == "HEAT":
                log_text = "MANUAL OVERRIDE HEAT"
                logger.write_splunk_log("info", log_text)
                nest.get_nest_status()
                nest.set_nest_status("HEAT", "OVERRIDE", "NONE")
                exit()
        elif row[0] == "CURRENT_SCHEDULE":
            current_schedule = row[1]


# ************* Process the current schedule sheet details ***************
    values = read_sheet(creds,current_schedule,logger)
    last_scheduled_time = 0
    end_row=[]

    for row in values:
     if row[0] != "SCHEDULED_TIME":
        row += [''] * (10 - len(row))
        scheduled_time = int(time.mktime(time.strptime(current_date + ' ' + row[0], '%Y-%m-%d %H:%M')))
        #print(f"Switch {row[1]} at {row[0]} ({scheduled_time}) {current_date_time} current day={current_day} today={row[current_day+1]}")

        if (row[current_day+1] == "Y") and (scheduled_time > current_date_time - 600) and (scheduled_time <= current_date_time) and (scheduled_time > last_scheduled_time):
            #print(f"Switch {row[1]} at {row[0]} ({scheduled_time}) {current_date_time} current day={current_day} today={row[current_day+1]}")
            end_row=row

    if end_row:
        #print(f"{end_row[0]}, {current_date + ' ' + end_row[0]}, {int(time.mktime(time.strptime(current_date + ' ' + end_row[0], '%Y-%m-%d %H:%M')))}, {end_row[1]}, {end_row[2]}")
        log_text = ("SWITCH " + end_row[1] + ", scheduled time was " + end_row[0] + "(" + str(int(time.mktime(time.strptime(current_date + ' ' + end_row[0], '%Y-%m-%d %H:%M')))) + ") from " + current_schedule)
        logger.write_splunk_log("info", log_text)
        nest.get_nest_status()
        nest.set_nest_status(end_row[1], current_schedule, current_date + ' ' + end_row[0])
    else:
        nest.get_nest_status()
        logger.write_splunk_log("info", "Nothing to do right now")



if __name__ == "__main__":
    main()
