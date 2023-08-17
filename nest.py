#!/usr/bin/env python3
import os
import requests
from pprint import pprint
import time


def write_splunk_log(log_type,log_text):

    if log_type == "setmode":
        nest_log_file = "/tmp/logs/nest_actions.log"
        log_text=time.strftime('%Y-%m-%d %H:%M:%S') + ", " + log_text
    elif log_type == "status":
        nest_log_file = "/tmp/logs/nest_status.log"
        log_text = log_text[:1] + "\"status_time\": \"" + str(time.strftime('%Y-%m-%d %H:%M:%S')) + "\", " + log_text[1:]
    elif log_type == "info":
        nest_log_file = "/tmp/logs/nest_info.log"
        log_text=time.strftime('%Y-%m-%d %H:%M:%S') + ", " + log_text
    else:
        nest_log_file = "/tmp/logs/nest_info.log"
        log_text=time.strftime('%Y-%m-%d %H:%M:%S') + ", " + "Error - Unknown Splunk Logging Type"

    log_text += "\n"

    f = open(nest_log_file, "a")
    f.write(log_text)
    f.close()

    return


def get_new_access_token():

    oauth2_client_id = os.getenv("G_CLIENT_ID")
    oauth2_client_secret = os.getenv("G_CLIENT_SECRET")
    refresh_token = os.getenv("G_REFRESH_TOKEN")

    url = f"https://www.googleapis.com/oauth2/v4/token?client_id={oauth2_client_id}"
    url += f"&client_secret={oauth2_client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"

    response = requests.post(url)

    if response.status_code == 200:
        log_text = "SUCCESS : response = " + response.text
        write_splunk_log("info",log_text)
    else:
        log_text = 'ERROR : Access Token Not Found - status code = '+str(response.status_code) + ", url = " + url
        write_splunk_log("info",log_text)

    return response.json()



def get_device_id(project_id,hdr):

    url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{project_id}/devices"

    response = requests.get(url, headers=hdr)

    if response.status_code == 200:
        log_text = "SUCCESS : response = " + response.text
        write_splunk_log("info",log_text)
    else:
        log_text = 'ERROR : Device ID Not Found - status code = '+str(response.status_code) + ", response = " + response.text
        write_splunk_log("info",log_text)

    return response.json()["devices"][0]["name"]





def set_nest_status(new_status_action,schedule_name,schedule_time):

    project_id = os.getenv("G_PROJECT_ID")
    access_token = get_new_access_token()
    hdr = {"Content-Type":"application/json","Authorization":f"{access_token['token_type']} {access_token['access_token']}"}

    device_id = get_device_id(project_id, hdr)


    url = f"https://smartdevicemanagement.googleapis.com/v1/{device_id}"

    device_data = requests.get(url, headers=hdr)

    if device_data.status_code == 200:
        r = device_data.text
        write_splunk_log("status", r)

    else:
        log_text = 'ERROR : Status Not Found - status code = '+str(device_data.status_code) + ", device data = " + device_data.text
        write_splunk_log("info",log_text)

    data = {
    "command" : "sdm.devices.commands.ThermostatMode.SetMode",
    "params" : {
      "mode" : new_status_action
    }
  }
    url += ":executeCommand"
    response = requests.post(url, headers=hdr, json=data)


    if response.status_code == 200:
        r = device_data.text
        log_text = "'mode':'" + new_status_action + "','nest_schedule_name':'" + schedule_name + "','nest_schedule_time':'" + schedule_time + "'"
        write_splunk_log("setmode",log_text)
    else:
        log_text = 'ERROR : Not Found - status code = '+str(response.status_code) + ", response = " + response.text
        write_splunk_log("info",log_text)


    return