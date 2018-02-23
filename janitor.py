#!/usr/bin/env python3
#
# Janitor, a bot to monitor a local network
#                  and control it from Telegram and terminal
# author: @jartigag

#TODO: (228) save prints (pinging) in .log
#TODO: (269) at_home, outside
#TODO: if CONFIG_FILE, IP_FILE, REMINDERS_FILE doesn't exist

import os
import argparse
import sys
import json
import subprocess
from time import time, sleep
from datetime import date, datetime
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
from threading import Thread

APP = "janitor"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APP + ".conf")
IP_FILE = os.path.join(CONFIG_APP_DIR, "ips.json")
REMINDERS_FILE = os.path.join(CONFIG_APP_DIR, "reminders.json")

ipsAtHome = os.path.join(CONFIG_APP_DIR, "ipsAtHome.json")
ipsOutside = os.path.join(CONFIG_APP_DIR, "ipsAtHome.json")

def add_ip(address,tag):
	# mkdir ~/.config/janitor/
	# echo "{\"ips\":[{\"tag\":\"\",\"address\":\"\"}]}"  > ~/.config/janitor/ips.json
	with open(IP_FILE, encoding="utf-8") as infile:
		data = json.load(infile)

		for i in range(0, len(data["ips"])):
			#TODO: check address format
			if data["ips"][i]["address"] == address:
				data["ips"][i].update({"tag":tag,"address":address})
				message = address + " renamed as " + tag
				print(message)
				break

			if i+1==len(data["ips"]):
				data["ips"].append({})
				data["ips"][i+1].update({"tag":tag,"address":address})
				message = "new ip: " + address + " added as " + tag
				print(message)

		if len(data["ips"])==0: #TODO: not the most elegant solution.. improve it
				data["ips"].append({})
				data["ips"][0].update({"tag":tag,"address":address})
				message = "new ip: " + address + " added as " + tag
				print(message)

		with open(IP_FILE, "w", encoding="utf-8") as outfile:
			json.dump(data, outfile, ensure_ascii=False)

	return message

def print_ips():
	with open(IP_FILE, encoding="utf-8") as f:
		data = json.load(f)
		message=""

		if not data["ips"]:
			message = "there's no ips saved"

		for ip in data["ips"]:
			message += ip["address"] + " saved as " + ip["tag"] + "\n"

		print(message)

	return message

def delete_ip(tag):
	with open(IP_FILE, encoding="utf-8") as infile:
		data = json.load(infile)

		if not data["ips"]:
			message = "there's no ips saved"
			print(message)

		for i in range(0, len(data["ips"])):

			if data["ips"][i]["tag"] == tag:
				message = "ip " + data["ips"][i]["address"] + " (" + tag + ") removed"
				print(message)
				data["ips"].pop(i)
				break

			if i+1==len(data["ips"]):
				message = "no ip with " + tag + " as tag"
				print(message)

		with open(IP_FILE, "w", encoding="utf-8") as outfile:
			json.dump(data, outfile, ensure_ascii=False)

	return message

def add_reminder(tag, reminder):
	# mkdir ~/.config/janitor/
	# echo "{\"ips\":[]}"  > ~/.config/janitor/reminders.json
	with open(REMINDERS_FILE, encoding="utf-8") as infile:
		data = json.load(infile)

		for i in range(0, len(data["ips"])):
			if data["ips"][i]["tag"] == tag:
				data["ips"][i]["reminder"].append(reminder)
				message = "reminder added to " + tag + ": " + reminder
				print(message)
				break

			if i+1==len(data["ips"]):
				data["ips"].append({})
				data["ips"][i+1].update({"tag":tag,"reminder":[reminder]})
				message = "new reminder to " + tag + ": " + reminder
				print(message)

		#TODO: it incorrectly add a reminder to inexistent tags
		#		-> check if tag exists in ips.json
		if len(data["ips"])==0: #TODO: not the most elegant solution.. improve it
				data["ips"].append({})
				data["ips"][0].update({"tag":tag,"reminder":[reminder]})
				message = "new reminder to " + tag + ": " + reminder
				print(message)

		with open(REMINDERS_FILE, "w", encoding="utf-8") as outfile:
			json.dump(data, outfile, ensure_ascii=False)

	return message

def reminders(tag):
	with open(REMINDERS_FILE, encoding="utf-8") as f:
		data = json.load(f)
		message=""

		if not data["ips"]:
			message = "there's no reminders for " + tag
		for i in range(0, len(data["ips"])):
			if data["ips"][i]["tag"] == tag:
				message=str(data["ips"][i]["reminder"])
				data["ips"][i]["reminder"] = []
		with open(REMINDERS_FILE, "w", encoding="utf-8") as outfile:
			json.dump({"ips":[]}, outfile, ensure_ascii=False)

		print(message)

	return message

def config():
	# mkdir ~/.config/janitor/
	# touch ~/.config/janitor/janitor.conf
	with open(CONFIG_FILE, encoding="utf-8") as c:
		token = input("enter your token \n(get it from @BotFather, as described in https://core.telegram.org/bots#6-botfather):\n")
		if token is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		chat_id = input("enter your chat_id (you can get it from @get_id_bot):\n")
		if chat_id is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		else:
			with open(CONFIG_FILE,"w", encoding="utf-8") as f:
				json.dump({"token":token,"chat_id":chat_id}, f, ensure_ascii=False)
				print("saved " + token + " as token in your config file")
				print("saved " + chat_id + " as chat_id in your config file")
				print("remember to start a telegram conversation with your bot")

def message(text):
	bot = JanitorBot()
	bot.send_message(text)

class JanitorBot(Bot):
    def __init__(self, token=None, chat_id=None):
    	if token is None or chat_id is None:
    		with open(CONFIG_FILE) as f:
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

def telegram_add_reminder(bot, update, args):
	try:
		#TODO: make args[1] to allow spaces
		message(add_reminder(args[0], args[1]))
	except (IndexError, ValueError):
		update.message.reply_text("usage: /add_reminder <tag> <reminder_message>")

#TODO: only 1 argument (tag)
def pinging(iptarget, tag):
	hometime = datetime.now()
	secondsout = 0 # seconds passed
	timeout = 40 # seconds to elapse before setting as gone
	atHome = True
	while True:
		p = subprocess.Popen(["ping", "-q", "-c", "3", iptarget], stdout = subprocess.PIPE, stderr=subprocess.PIPE)
		droppedPackets = p.wait()

		#TODO: save prints in .log
		if not droppedPackets:
			print(tag + " at home! -", datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			hometime = datetime.now()
			if not atHome:
				message("welcome home, " + tag + "!")
				atHome = True
				message(reminders(tag))
		else:
			secondsout = (datetime.now() - hometime).seconds
			print(tag + " isn't here since %d seconds -" % secondsout, datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			#TODO: format to minutes, hours
			if secondsout > timeout and atHome:
				print(tag + " is gone.")
				message("goodbye " + tag + "!")
				atHome = False

		#TODO at_home, outside:
		sleep(10)

def start():
	with open(CONFIG_FILE, encoding="utf-8") as f:
		config = json.load(f)
		token = config["token"]

	updater= Updater(token=token)
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler('add_ip', telegram_add_ip, pass_args=True))
	dispatcher.add_handler(CommandHandler('print_ips', telegram_print_ips))
	dispatcher.add_handler(CommandHandler('delete_ip', telegram_delete_ip, pass_args=True))
	dispatcher.add_handler(CommandHandler('add_reminder', telegram_add_reminder, pass_args=True))

	with open(IP_FILE, encoding="utf-8") as f:
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
	group.add_argument("-c", "--config", action="store_true",
						help="set telegram params (token, chat_id)")
	group.add_argument("-a", "--add_ip", metavar=("ip_address","tag"), nargs=2,
	                    help="add an ip address with a tag. example: 192.168.1.1 router")
	group.add_argument("-p", "--print_ips", action="store_true",
						help="print saved ips")
	group.add_argument("-d", "--delete_ip", metavar="tag",
						help="delete ip identified with given tag.")
	#group.add_argument("-e", "--at_home", action="store_true",
	#					help="print who is at home")
	group.add_argument("-r", "--add_reminder", metavar=("tag","reminder"), nargs=2,
	                    help="add a reminder to a saved ip coming home. example: john \"hang up the washing!\"")
	#group.add_argument( "-o", "--outside",action="store_true",
	#					help="print who is outside")
	group.add_argument("-s", "--start", action="store_true",
						help="start running the script")

	args = parser.parse_args()

	if args.add_ip:
		address = args.add_ip[0]
		tag = args.add_ip[1]
		add_ip(address,tag)
	if args.config:
		config()
	#if args.at_home:
	#	at_home()
	if args.add_reminder:
		tag = args.add_reminder[0]
		reminder = args.add_reminder[1]
		add_reminder(tag,reminder)
	#if args.outside:
	#	outside()
	if args.print_ips:
		print_ips()
	if args.delete_ip:
		delete_ip(args.delete_ip)
	if args.start:
		start()
	if len(sys.argv)==1:
	    parser.print_help()
	    sys.exit(1)