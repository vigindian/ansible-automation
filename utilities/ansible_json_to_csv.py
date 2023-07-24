#!/usr/bin/env python3

# Convert json to csv

#input arguments
import sys

#json processing
import json

#{'host': 'server1-pro.prod.linux.com', 'uptime': '4 days'}
#ensure (ansible) input is in a valid json format
inputArg = sys.argv[1].replace('\'', '"')
inputJson = json.loads(inputArg)

for details in inputJson:
    host = details["host"]
    uptime = details["uptime"]
    print("\"" + str(host) + "\",\"" + str(uptime)  + "\"")
