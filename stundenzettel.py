#!/usr/bin/python

import os, json, argparse, datetime

print('hallo')

parser = argparse.ArgumentParser(description='Ein digitaler Stundenzettel')

parser.add_argument('-l',help='Einmal alle Daten ausgeben',action='store_true',default=False)

args = parser.parse_args()

print(args)

def load_data():
	if os.path.isfile('stundenzettel'):
		stundenzettel_string = ''
		with open('stundenzettel','r') as file:
			stundenzettel_string = file.read()
		return json.loads(stundenzettel_string)
	else:
		return []

print(load_data())

print(datetime.date.today())
