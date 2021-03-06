# This file uses the experiment-cli tool to genrate the IoTLab motes locations.
# Refere to the Mercator wiki to use it.
# https://github.com/openwsn-berkeley/mercator/wiki

#-----------------------------------------------------------------------------#

import os
import json

#-----------------------------------------------------------------------------#

STATES = ["Busy","Alive"]

# get IoTlab infos

os.system("experiment-cli info -l > tmp.json")
jout = ""
with open('tmp.json') as data_file:
    jout = json.load(data_file)
os.remove("tmp.json")

# parse results

results = {}
for mote in jout["items"]:
    if mote["state"] in STATES:
        # create site if it does not exists
        if mote["site"] not in results.keys():
            results[mote["site"]] = []

        # add mote to site
        results[mote["site"]].append(mote["network_address"])

# write out

with open('states.json', 'w') as fp:
    json.dump(results, fp, indent=4)

#-----------------------------------------------------------------------------#
