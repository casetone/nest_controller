#!/usr/bin/env python3
import os
import requests
from pprint import pprint
import time



def get_new_access_token():

    oauth2_client_id = os.getenv("G_CLIENT_ID")
    oauth2_client_secret = os.getenv("G_CLIENT_SECRET")
    refresh_token = os.getenv("G_REFRESH_TOKEN")

    url = f"https://www.googleapis.com/oauth2/v4/token?client_id={oauth2_client_id}"
    url += f"&client_secret={oauth2_client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"

    response = requests.post(url)

    if response.status_code == 200:
        r = response.json()
        print(r)
    else:
        print(url)
        print('Not Found - status code = '+str(response.status_code))

    return response.json()



def get_device_id(project_id,hdr):

    url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{project_id}/devices"

    response = requests.get(url, headers=hdr)

    if response.status_code == 200:
        r = response.json()
        pprint(r)
    else:
        print(response.text)
        print('Not Found - status code = '+str(response.status_code))
    #print(response)
    return response.json()["devices"][0]["name"]



def write_splunk_log(log_type,log_text):

    if log_type == "setmode":
        nest_log_file = "/tmp/logs/nest_actions.log"
        log_text=time.strftime('%Y-%m-%d %H:%M:%S') + ", " + log_text

    elif log_type == "status":
        nest_log_file = "/tmp/logs/nest_status.log"
        log_text = log_text[:1] + "\"status_time\": \"" + str(time.strftime('%Y-%m-%d %H:%M:%S')) + "\", " + log_text[1:]
        #log_text = log_text.replace("'","\"")

    log_text += "\n"

    f = open(nest_log_file, "a")
    f.write(log_text)
    f.close()
    #print(log_text)



def set_nest_status(new_status_action,schedule_name,schedule_time):

    project_id = os.getenv("G_PROJECT_ID")
    access_token = get_new_access_token()
    hdr = {"Content-Type":"application/json","Authorization":f"{access_token['token_type']} {access_token['access_token']}"}

    device_id = get_device_id(project_id, hdr)


    url = f"https://smartdevicemanagement.googleapis.com/v1/{device_id}"

    device_data = requests.get(url, headers=hdr)

    if device_data.status_code == 200:
        r = device_data.text
        #pprint(r)
        write_splunk_log("status", r)

    else:
        print(device_data.text)
        print('Not Found - status code = '+str(device_data.status_code))

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
        #pprint(r)
        log_text = "'mode':'" + new_status_action + "','nest_schedule_name':'" + schedule_name + "','nest_schedule_time':'" + schedule_time + "'"
        write_splunk_log("setmode",log_text)
    else:
        print(response.text)
        print('Not Found - status code = '+str(response.status_code))


    return