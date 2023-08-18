#!/usr/bin/env python3
import os
import requests
from pprint import pprint
import time


class Logger:
        
    #def __init__(self):


    def write_splunk_log(self,log_type,log_text):

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
        print(log_text)
        return


class Nest:
    def __init__(self,logger):
        self.logger = logger
        self.project_id = os.getenv("G_PROJECT_ID")
        self.get_new_access_token()

        self.headers = {"Content-Type":"application/json","Authorization":f"{self.access_token['token_type']} {self.access_token['access_token']}"}
        self.get_device_id()



    def get_new_access_token(self):

        oauth2_client_id = os.getenv("G_CLIENT_ID")
        oauth2_client_secret = os.getenv("G_CLIENT_SECRET")
        refresh_token = os.getenv("G_REFRESH_TOKEN")

        url = f"https://www.googleapis.com/oauth2/v4/token?client_id={oauth2_client_id}"
        url += f"&client_secret={oauth2_client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"

        response = requests.post(url)

        if response.status_code == 200:
            self.access_token = response.json()
            log_text = "SUCCESS : response = " + response.text
            self.logger.write_splunk_log("info",log_text)
        else:
            log_text = 'ERROR : Access Token Not Found - status code = '+str(response.status_code) + ", url = " + url
            exit

        return response.json()



    def get_device_id(self):

        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{self.project_id}/devices"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            self.device_id = response.json()["devices"][0]["name"]
            log_text = "SUCCESS : response = " + response.text
            self.logger.write_splunk_log("info",log_text)
        else:
            log_text = 'ERROR : Device ID Not Found - status code = '+str(response.status_code) + ", response = " + response.text
            self.logger.write_splunk_log("info",log_text)
            exit
        
        return



    def get_nest_status(self):

        url = f"https://smartdevicemanagement.googleapis.com/v1/{self.device_id}"

        r = requests.get(url, headers=self.headers)

        if r.status_code == 200:
            self.device_data = r.json()
            self.logger.write_splunk_log("status", r.text)
        else:
            log_text = 'ERROR : Status Not Found - status code = '+str(r.status_code) + ", device data = " + r.text
            self.logger.write_splunk_log("info",log_text)
            exit

        return



    def set_nest_status(self,new_status_action,schedule_name,schedule_time):

        data = {
        "command" : "sdm.devices.commands.ThermostatMode.SetMode",
        "params" : {
        "mode" : new_status_action
        }
    }
        url = f"https://smartdevicemanagement.googleapis.com/v1/{self.device_id}:executeCommand"
        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            log_text = "'mode':'" + new_status_action + "','nest_schedule_name':'" + schedule_name + "','nest_schedule_time':'" + schedule_time + "'"
            self.logger.write_splunk_log("setmode",log_text)
        else:
            log_text = 'ERROR : Not Found - status code = '+str(response.status_code) + ", response = " + response.text
            self.logger.write_splunk_log("info",log_text)
            exit

        return response.status_code