#!/usr/bin/env python3

# Ansible Dynamic Inventory script to generate inventory based on a flat-file input file with hosts
# - This script accepts options "--list" and "--host" which are required by Ansible.
# - Linux server naming convention is used to split servers into sub-groups.
# - In hostname, the 2nd column separated by "-" has the app-name. So each sub-group will have all hosts of the same app.
# - All hosts added to common-group "linux".
# - Add ansible connection parameters as sub-group variables.

#handle script arguments
import argparse

#json stuff
import json

#file
from os import path
#import os

############
# FUNCTIONS
############
def empty_inventory():
  return {'_meta': {'hostvars': {}}}

def generate_Inventory(inputFile):
  thisInv = json.loads('{}')
  with open(inputFile) as ifile:
    for host in ifile:
      hostName = host.strip()
      try:
        #2nd column of the hostname has app
        subGroup = hostName.split("-")[1].split(".")[0]
      except IndexError:
        #ignore host that does not follow our naming convention
        continue

      #common-group
      if commonGroup not in thisInv:
        thisInv[commonGroup] = {
          "children": []
        }

      #append sub-group as main-group's child
      if subGroup not in thisInv[commonGroup]["children"]:
        thisInv[commonGroup]["children"].append(subGroup)

      #new sub-group: define base structure
      if subGroup not in thisInv:
        thisInv[subGroup] = {
          "hosts": [],
          "vars": {
            "ansible_connection": "ssh",
            "ansible_user": "ansible"
          }
        }

      #append hostname
      if hostName not in thisInv[subGroup]["hosts"]:
        thisInv[subGroup]["hosts"].append(hostName)

  return thisInv

########
# MAIN
########
inventory = {}

#parse input arguments
parser = argparse.ArgumentParser()

parser.add_argument(
        "-l",
        "--list",
	      action = "store_true",
        help = "list the inventory")

parser.add_argument(
        "-f",
        "--file",
        required = False,
        default = "./linux-servers.txt",
        action = "store",
        help = "Input file for inventory")

parser.add_argument(
        "-g",
        "--group",
        required = False,
        default = "linux",
        action = "store",
        help = "Common group for all sub-groups")

parser.add_argument(
        "-H",
        "--host",
	      default = None,
	      action = "store",
        help = "Get specific host info")

options = parser.parse_args()

file = options.file
commonGroup = options.group

# Check if input-file exists
if path.isfile(file) is False:
  raise Exception("File not found")

if options.list:
  #generate inventory from the input-file
  inventory = generate_Inventory(file)
elif options.host:
  inventory = empty_inventory()
#else:
#  inventory = empty_inventory()

#finally print the inventory
print (json.dumps(inventory))
