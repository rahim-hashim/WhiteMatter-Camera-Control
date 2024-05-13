import os
import time
import json
import argparse
from datetime import datetime
import urllib3,requests
# (optional) Disable the "insecure requests" warning for https certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from whitematter_login import remote_url

# looking up cameras from name
def getCamByName(jsonobj, name):
    for dict in jsonobj:
        if name in dict['Hostname']:
            return dict

# get the cam id # from name
def getCamIdByName(jsonobj, name):
    return getCamByName(jsonobj, name)['Id']

# what watchtower url to control
watchtowerurl = f'https://{remote_url}:4343' # for local: "https:\\localhost:4343' # for remote: https:\\[WATCHTOWER_ID]:4343 
master_cameraname = 'e3v8360'

# parse arguments for trial number
parser = argparse.ArgumentParser(description='Provide the trial number for saving.')
parser.add_argument('monkey_name',type=str, nargs=1,
                    help='the name of the monkey in the experiment') 
args = parser.parse_args()
monkey_name = args.monkey_name[0]

# set api file path on remote computer
api_save_root = os.getcwd()
# datetime object containing current date and time
now = datetime.now()
d_string = now.strftime("%y%m%d")
dt_string = now.strftime("%y%m%d_%H%M%S")
session_id = d_string+'_'+monkey_name
api_save_file = os.path.join(api_save_root, session_id)

with open(f'{api_save_file}.json', 'r') as file:
    session_info = json.load(file)
    apit = session_info['apit']
    all_camids = session_info['camids']

# # Stop saving
requests.post(watchtowerurl+'/api/cameras/action', 
                data = {'IdGroup[]': all_camids, 
                        'Action': 'STOPRECORDGROUP', 
                        'apitoken': apit}, 
                verify=False
             )
print("Stopped saving")