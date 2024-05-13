import os
import sys
import time
import json
import argparse
from datetime import datetime
import urllib3, requests
# update whitematter_login.py with your White Matter username/password
from whitematter_login import wm_username, wm_password, remote_url
# (optional) Disable the "insecure requests" warning for https certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f'  Login Info:')
print(f'    Username: {wm_username}')
wm_password_encrypted = len(wm_password)*'*'
print(f'    Password: {wm_password_encrypted}')

# looking up cameras from name
def getCamByName(jsonobj, name):
	for dict in jsonobj:
		if name in dict['Hostname']:
			return dict

# get the cam id # from name
def getCamIdByName(jsonobj, name):
	return getCamByName(jsonobj, name)['Id']

def print_cams(cam_list):
	"""prints the list of cameras"""
	print("Available cameras:")
	for cam in cam_list:
	  print("  Id {:d}: {:s}".format(cam['Id'], cam['Hostname']))

def api_login(url, username, password):
	"""logs into the watchtower API and returns the API token"""
	# login and obtain API token
	r = requests.post(url+'/api/login', data = {'username': wm_username, 'password': wm_password}, verify=False)
	if r.status_code != 200:
		print(f'  <API Login> response code error: {r}')
		return -1
	else:
		print(f' >> API Login success')
		j = json.loads(r.text)
		apit = j['apitoken']
		return apit

def get_cam_list(url, apit):
	"""gets the list of cameras and returns the camera ids"""
	r = requests.get(url+'/api/cameras', params = {'apitoken': apit}, verify=False)
	cam_list = json.loads(r.text)
	# # Scan for cameras
	# r = requests.get(watchtowerurl+'/api/cameras/scan', params = {'apitoken': apit}, verify=False)
	# Search for a specific camera Id by name
	master_camid = getCamIdByName(cam_list, master_cameraname)
	# update_sync_source(watchtowerurl, apit, master_camid, master_cameraname)
	all_camids = [cam['Id'] for cam in cam_list]
	print_cams(cam_list)
	# Make sure cameras are running and synced
	r = requests.get(watchtowerurl+'/api/cameras', params = {'apitoken': apit}, verify=False)
	j = json.loads(r.text)
	cam = getCamByName(j, master_cameraname)
	print("Running state: {:d}".format(cam['Runstate']))
	return all_camids

def update_sync_source(url, apit, master_camid, master_cameraname):
	"""updates the sync source to the master camera"""
	# Update the sync source
	requests.post(url+'/api/cameras/action', data = {'Id': master_camid, 'Action': 'UPDATEMC', 'apitoken': apit}, verify=False)
	print(">> Choosing {:d}: {:s} as sync source\n".format(master_camid, master_cameraname))

def save_api(url, trial_num, session_id, monkey_name):
	"""saves the api token and camera ids to a json file"""
	# set api file path on remote computer
	api_save_file = os.path.join(os.getcwd(), session_id)
	# get api token
	apit = api_login(url, wm_username, wm_password)
	if apit == -1:
		print('<API Login> error')
		sys.exit()
	# update global save path
	# update_global_save_path(watchtowerurl, save_folder, apit)
	all_camids = get_cam_list(url, apit)
	session_info = {}
	session_info['apit'] = apit
	session_info['camids'] = all_camids
	# Writing the dictionary to a file
	with open(f'{api_save_file}.json', 'w') as file:
		json.dump(session_info, file)
	return all_camids, apit

# def save_api(url, trial_num, session_id, monkey_name):
# 	"""saves the api token and camera ids to a json file"""
# 	# set api file path on remote computer
# 	api_save_file = os.path.join(os.getcwd(), session_id)
# 	# only on first trial
# 	if trial_num == '1':
# 		# get api token
# 		apit = api_login(url, username, password)
# 		if apit == -1:
# 			print('<API Login> error')
# 			sys.exit()
# 		# update global save path
# 		# update_global_save_path(watchtowerurl, save_folder, apit)
# 		all_camids = get_cam_list(url, apit)
# 		session_info = {}
# 		session_info['apit'] = apit
# 		session_info['camids'] = all_camids
# 		# Writing the dictionary to a file
# 		with open(f'{api_save_file}.json', 'w') as file:
# 			json.dump(session_info, file)
# 	# all other trials
# 	else:
# 		# Reading the dictionary from the file
# 		with open(f'{api_save_file}.json', 'r') as file:
# 			session_info = json.load(file)
# 			apit = session_info['apit']
# 			all_camids = session_info['camids']
# 	return all_camids, apit

def update_global_save_path(url, global_save_path, apit):
	"""sets the global save path on the host computer"""
	response = requests.post(url+'/api/sessions/rename', 
							data = {'Filepath': global_save_path},
							params = {'apitoken': apit}, 
							verify=False)
	if response.status_code != 200:
		print(f'  <Global Save Path> response code error: {response}')
	else:
		print(f' >> Setting global save path: {global_save_path}')

def update_segmentation_duration(url, segment_duration, apit):
	response = requests.post(url+'/api/sessions/segment', 
		data = {'Segment': f'{segment_duration}'}, 
		params = {'apitoken': apit}, 
		verify=False)
	if response.status_code != 200:
		print(f'  <Segment Duration> response code error: {response}')
	else:
		print(f' >> Updating segment duration to {segment_duration} minute(s)')

def start_save(url, all_camids, save_folder, apit):
	"""triggers saving on all cameras in the group"""
	response = requests.post(watchtowerurl+'/api/cameras/action', 
					data = {'IdGroup[]': all_camids, 'Action': 'RECORDGROUP'},
					params = {'AdditionalPath': save_folder, 'apitoken': apit}, 
					verify=False)
	if response.status_code != 200:
		print(f'  Saving response code error: {response}')
	else:
		print('Saving to: {}'.format(save_folder))

# parse arguments for trial number
parser = argparse.ArgumentParser(description='Provide the trial number for saving.')
parser.add_argument('monkey_name',type=str, nargs=1,
					help='the name of the monkey in the experiment')
parser.add_argument('trial_num',type=str, nargs=1,
					help='an integer of the trial number')
args = parser.parse_args()
monkey_name = args.monkey_name[0]
trial_num = args.trial_num[0]

# what watchtower url to control
## for local: "https:\\localhost:4343' # for remote: https:\\[WATCHTOWER_ID]:4343
watchtowerurl = f'https://{remote_url}:4343'  
master_cameraname = 'e3v8360'

# set global save path on host computer
save_root = 'C:\\Users\\rober\\Desktop\\rhAirpuff\\videos'

# datetime object containing current date and time
now = datetime.now()
d_string = now.strftime("%y%m%d")
t_string = now.strftime("%H%M%S")
session_id = d_string+'_'+monkey_name
global_save_path = os.path.join(save_root, session_id)

# Bind to camera
# requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': master_camid, 'Action': 'BIND', 'apitoken': apit}, verify=False)

# Connect to a camera
resolution = '480p120'	# 640x480 resolution, 120 fps
codec = 'H264'          # H264 | MJPEG
anno = 'None'			# Name | Time | CameraName | None
segment = '1h'
# requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': master_camid, 'Action': 'CONNECT', 'Iface': '', 'Config': resolution, 'Codec': codec, 'Annotation': anno, 'Segtime': segment, 'apitoken': apit}, verify=False)

all_camids, apit = save_api(watchtowerurl, trial_num, session_id, monkey_name)

trial_num_str = f"{int(trial_num):04}"
save_folder = os.path.join(global_save_path, d_string+'_'+monkey_name+'_'+t_string)

# when AdditionalPath param is not working for RECORDGROUP
update_global_save_path(watchtowerurl, save_folder, apit)

# set global segment duration
update_segmentation_duration(watchtowerurl, '20m', apit)

# Start saving
try:
	start_save(watchtowerurl, all_camids, save_folder, apit)
except:
	print('  >> Start Save Issue. Did not start.')