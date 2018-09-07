#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Janitor, a bot to monitor a local network
# and control it from Telegram and terminal
#
# @jartigag
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#WIP: (128) add_reminder
#TODO: (273) at_home, outside
#TODO: virtualenv: mkvirtualenv -p python3 janitor;
#				workon janitor; pip install -r requirements.txt

import os
import re
import logging
import argparse
import json
import subprocess
from time import time, sleep
from datetime import date, datetime
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
from threading import Thread

APP = "janitor"
try:
	os.mkdir(os.path.expanduser("~")+'/.config')
except FileExistsError:
	pass
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
try:
	os.mkdir(CONFIG_DIR+'/'+APP)
except FileExistsError:
	pass
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APP + ".conf")
LOGGING_FILE = os.path.join(CONFIG_APP_DIR, APP + ".log")
IP_FILE = os.path.join(CONFIG_APP_DIR, "ips.json")
REMINDERS_FILE = os.path.join(CONFIG_APP_DIR, "reminders.json")

ipsAtHome = os.path.join(CONFIG_APP_DIR, "ipsAtHome.json")
ipsOutside = os.path.join(CONFIG_APP_DIR, "ipsAtHome.json")

def add_ip(address,tag):
	# IP address pattern
	pattern = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
	# check if it's a valid ip address
	if pattern.match(address):
		data = json.load(open(IP_FILE, "r"))
		# if there's no ips: add it
		if not data["ips"]:
				data["ips"]=[]
				data["ips"].append({})
				data["ips"][0].update({"tag":tag,"address":address})
				message = "new ip: " + address + " added as " + tag
				print(message)
		else:
			# if there are ips: loop throught it
			for ip in data["ips"]:
				# if address is in IP_FILE: rename it
				if ip["address"] == address:
					ip.update({"tag":tag,"address":address})
					message = address + " renamed as " + tag
					print(message)
					break
				# if it's last element (that is, address isn't in IP_FILE): add it
				if ip == data["ips"][-1]:
					data["ips"].append({})
					data["ips"][i+1].update({"tag":tag,"address":address})
					message = "new ip: " + address + " added as " + tag
					print(message)

		# save changes:
		json.dump(data, open(IP_FILE, "w"), ensure_ascii=False)
	else:
		message = "invalid ip"
		print(message)

	return message

def print_ips():
	with open(IP_FILE, "r") as f:
		data = json.load(f)
		message=""
		if not data["ips"]:
			message = "there's no ips saved"
		for ip in data["ips"]:
			message += ip["address"] + " saved as " + ip["tag"] + "\n"
		print(message)
	return message

def delete_ip(tag):
	data = json.load(open(IP_FILE, "r"))
	# if there's no ips:
	if not data["ips"]:
		message = "there's no ips saved"
		print(message)
	else:
		# if there are ips: loop throught it
		for ip in data["ips"]:
			# if tag is in IP_FILE: remove it
			if ip["tag"] == tag:
				message = "ip " + ip["address"] + " (" + tag + ") removed"
				print(message)
				data["ips"].pop(data["ips"].index(ip))
				break
			# if it's last element (that is, tag isn't in IP_FILE): warn it
			if ip == data["ips"][-1]:
				message = "no ip with " + tag + " as tag"
				print(message)

	# save changes:
		json.dump(data, open(IP_FILE, "w"), ensure_ascii=False)

	return message

def add_reminder(tag, reminder):
	#WIP:
	with json.load(open(REMINDERS_FILE,"r+")) as data:
		# if there's no ips: add tag and reminder
		if not data["ips"]:
			data["ips"].append({})
			data["ips"][0].update({"tag":tag,"reminder":[reminder]})
			message = "new reminder to " + tag + ": " + reminder
			print(message)
		else:
			# if there are ips: loop throught it
			for ip in data["ips"]:
				# if tag is in REMINDERS_FILE: add reminder
				if ip["tag"] == tag:
					ip["reminder"].append(reminder)
					message = "reminder added to " + tag + ": " + reminder
					print(message)
					break
				# if it's last element (that is, tag isn't in REMINDERS_FILE): add tag and reminder
				if ip == data["ips"][-1]:
					data["ips"].append({})
					data["ips"][i+1].update({"tag":tag,"reminder":[reminder]})
					message = "new reminder to " + tag + ": " + reminder
					print(message)

		#TODO: it incorrectly add a reminder to inexistent tags
		#		-> check if tag exists in ips.json

		# save changes:
		with open(REMINDERS_FILE, "w") as outfile:
			json.dump(data, outfile, ensure_ascii=False)

	return message

def reminders(tag):
	with open(REMINDERS_FILE, "w") as f:
		data = json.load(f)
		message=""
		for ip in data["ips"]:
			if ip["tag"] == tag:
				message=str(ip["reminder"])
				ip["reminder"] = [] # clear ip's reminders

		# save changes:
		with open(REMINDERS_FILE, "w") as outfile:
			json.dump({"ips":[]}, outfile, ensure_ascii=False)

		print(message)

	return message

def config():
	with open(CONFIG_FILE, "w") as c:
		token = input("enter your token \n(get it from @BotFather, \
as described in https://core.telegram.org/bots#6-botfather):\n")
		if token is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		chat_id = input("enter your chat_id (you can get it from @myidbot):\n")
		if chat_id is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		else:
			json.dump({"token":token,"chat_id":chat_id}, c, ensure_ascii=False)
			print("saved " + token + " as token in your config file")
			print("saved " + chat_id + " as chat_id in your config file")
			print("remember to start a telegram conversation with your bot\n\n")

def message(text):
	bot = JanitorBot()
	bot.send_message(text)

class JanitorBot(Bot):
    def __init__(self, token=None, chat_id=None):
    	if token is None or chat_id is None:
			with open(CONFIG_FILE, "r+") as f:
    			config = json.load(f)
    			token = config["token"]
    			chat_id = config["chat_id"]
    	Bot.__init__(self, token)
    	self.chat_id = chat_id

    def send_message(self, text):
        super(JanitorBot, self).send_message(chat_id=self.chat_id,
                                            text=text,
                                            parse_mode=ParseMode.MARKDOWN)

def telegram_add_ip(bot, update, args):
	try:
		message(add_ip(args[0], args[1]))
	except (IndexError, ValueError):
		update.message.reply_text("usage: /add_ip <localIP> <tag>")

def telegram_print_ips(bot, update):
	try:
		message(print_ips())
	except (IndexError, ValueError):
		update.message.reply_text("usage: /print_ips")

def telegram_delete_ip(bot, update, args):
	try:
		message(delete_ip(args[0]))
	except (IndexError, ValueError):
		update.message.reply_text("usage: /delete_ip <tag>")

def telegram_reminder(bot, update, args):
	try:
		#TODO: make args[1] to allow spaces
		message(add_reminder(args[0], args[1]))
	except (IndexError, ValueError):
		update.message.reply_text("usage: /reminder <tag> <reminder_message>")

#TODO: only 1 argument (tag)
def pinging(iptarget, tag):
	hometime = datetime.now()
	secondsout = 0 # seconds passed
	timeout = 40 # seconds to elapse before setting as gone
	atHome = True
	while True:
		p = subprocess.Popen(["ping", "-q", "-c", "3", iptarget],
			stdout = subprocess.PIPE, stderr=subprocess.PIPE)
		droppedPackets = p.wait()

		if not droppedPackets:
			print(tag + " at home! -", datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			logger.warning(tag + " at home! - " + datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			hometime = datetime.now()
			if not atHome:
				message("welcome home, " + tag + "!")
				atHome = True
				#message(reminders(tag))
		else:
			secondsout = (datetime.now() - hometime).seconds
			print(tag + " isn't here since %d seconds -" %
				secondsout, datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			logger.warning(tag + " isn't here since "+str(secondsout)+" seconds - "\
				+ datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			#TODO: format to minutes, hours
			if secondsout > timeout and atHome:
				print(tag + " is gone.")
				logger.warning(tag + " is gone.")
				message("goodbye " + tag + "!")
				atHome = False

		#TODO at_home, outside:
		sleep(10)

def start():
	with open(CONFIG_FILE, "r+") as f:
		config = json.load(f)
		token = config["token"]

	updater= Updater(token=token)
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler('add_ip', telegram_add_ip, pass_args=True))
	dispatcher.add_handler(CommandHandler('print_ips', telegram_print_ips))
	dispatcher.add_handler(CommandHandler('delete_ip', telegram_delete_ip, pass_args=True))
	dispatcher.add_handler(CommandHandler('reminder', telegram_reminder, pass_args=True))

	with open(IP_FILE, "r+") as f:
		data = json.load(f)
		if len(data["ips"])==0:
			message("there's no ip, can't ping it")
		for i in range(0, len(data["ips"])):
			Thread(target=pinging, args=(data["ips"][i]["address"],data["ips"][i]["tag"])).start()
		
	Thread(target=updater.start_polling).start()

def at_home():
	#TODO
	print("ips at home")

def outside():
	#TODO
	print("ips outside")


if __name__ == "__main__":
	# Options
	parser = argparse.ArgumentParser(description="simple bot to monitor a local network")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-a", "--add_ip", metavar=("ip_address","tag"), nargs=2,
	                    help="add an ip address with a tag. example: 192.168.1.1 router")
	group.add_argument("-p", "--print_ips", action="store_true",
						help="print saved ips")
	group.add_argument("-d", "--delete_ip", metavar="tag",
						help="delete ip identified with given tag.")
	#group.add_argument("-e", "--at_home", action="store_true",
	#					help="print who is at home")
	group.add_argument("-r", "--reminder", metavar=("tag","reminder"), nargs=2,
	                    help="add a reminder to a saved ip coming home. \
	                    example: john \"hang up the washing!\"")
	#group.add_argument( "-o", "--outside",action="store_true",
	#					help="print who is outside")
	group.add_argument("-s", "--start", action="store_true",
						help="start running the script")

	args = parser.parse_args()

	logger = logging.getLogger()
	logger.setLevel(logging.WARNING) #TODO: INFO level?
	logFile = logging.FileHandler(LOGGING_FILE)
	logger.addHandler(logFile)

	try:
		with open(CONFIG_FILE, "r+") as f:
			if f.read()=="":
				config()
	except FileNotFoundError:
		config()

	try:
		with open(IP_FILE, "r+") as f:
			if f.read()=="": print("{\"ips\":[]}",file=f)
	except FileNotFoundError:
		with open(IP_FILE, "w") as f:
			print("{\"ips\":[]}",file=f)

	if args.add_ip:
		address = args.add_ip[0]
		tag = args.add_ip[1]
		add_ip(address,tag)
	#if args.at_home:
	#	at_home()
	if args.reminder:
		tag = args.reminder[0]
		reminder = args.reminder[1]
		add_reminder(tag,reminder)
	#if args.outside:
	#	outside()
	if args.print_ips:
		print_ips()
	if args.delete_ip:
		delete_ip(args.delete_ip)
	if args.start:
		start()
	if not any(vars(args).values()):
	    parser.print_help()
