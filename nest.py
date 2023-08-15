#!/usr/bin/env python3
import os
import requests
from pprint import pprint


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


def main():

    project_id = os.getenv("G_PROJECT_ID")
    access_token = get_new_access_token()
    hdr = {"Content-Type":"application/json","Authorization":f"{access_token['token_type']} {access_token['access_token']}"}

    device_id = get_device_id(project_id, hdr)


    url = f"https://smartdevicemanagement.googleapis.com/v1/{device_id}"

    device_data = requests.get(url, headers=hdr)

    if device_data.status_code == 200:
        r = device_data.json()
        pprint(r)
    else:
        print(device_data.text)
        print('Not Found - status code = '+str(device_data.status_code))


    data = {
    "command" : "sdm.devices.commands.ThermostatMode.SetMode",
    "params" : {
      "mode" : "OFF"
    }
  }
    url += ":executeCommand"
    response = requests.post(url, headers=hdr, json=data)


    if response.status_code == 200:
        r = response.json()
        pprint(r)
    else:
        print(response.text)
        print('Not Found - status code = '+str(response.status_code))


if __name__ == "__main__":
    main()
