#!/usr/bin/env python3
#
# Janitor, a bot to monitor a local network
#                  and control it from Telegram and terminal (at least for now)
# author: @jartigag

#TODO: (34) save prints (pinging) in .log

import os
import argparse
import json
import subprocess
from time import time, sleep
from datetime import date, datetime
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
from threading import Thread

APP = "janitor"
APPCONF = APP + ".conf"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APPCONF)
IP_FILE = os.path.join(CONFIG_APP_DIR, "ips.json")

def add_ip(address,tag):
	# mkdir ~/.config/janitor/
	# echo "{\"ips\":[{\"tag\":\"\",\"address\":\"\"}]}"  > ~/.config/janitor/ips.json
	#TODO: if IP_FILE doesn't exist
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

def remove_ip(tag):
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

def config():
	# mkdir ~/.config/janitor/
	# touch ~/.config/janitor/janitor.conf
	#TODO: if CONFIG_FILE doesn't exist
	with open(CONFIG_FILE, encoding="utf-8") as c:
		token = input("enter your token \n(get it from @BotFather, as described in https://core.telegram.org/bots#6-botfather):\n")
		if token is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		channel_id = input("enter your channel_id (you can get it from @get_id_bot):\n")
		if channel_id is "":
			print("exit config. changes not saved")
			print("actual config:\n" + str(json.load(c)))
			return
		else:
			with open(CONFIG_FILE,"w", encoding="utf-8") as f:
				json.dump({"token":token,"channel_id":channel_id}, f, ensure_ascii=False)
				print("saved " + token + " as token in your config file")
				print("saved " + channel_id + " as channel_id in your config file")
				print("remember to start a telegram conversation with your bot")

'''
def hello(bot, update):
    bot.send_message(update.message.chat_id, "Hello? We can hear you! Hello?!")
    bot.send_document(update.message.chat_id, open('gifs/hello2.mp4', 'rb'))
'''

def message(text):
	bot = JanitorBot()
	bot.send_message(text)

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
		else:
			secondsout = (datetime.now() - hometime).seconds
			print(tag + " isn't here since %d seconds -" % secondsout, datetime.now().strftime('%a, %d %b %Y %H:%M:%S'))
			#TODO: format to minutes, hours
			if secondsout > timeout and atHome:
				print(tag + " gone.")
				message("goodbye " + tag + "!")
				atHome = False
		sleep(10)

class JanitorBot(Bot):
    def __init__(self, token=None, channel_id=None):
    	if token is None or channel_id is None:
    		with open(CONFIG_FILE) as f:
    			config = json.load(f)
    			token = config["token"]
    			channel_id = config["channel_id"]
    	Bot.__init__(self, token)
    	self.channel_id = channel_id

    def send_message(self, text):
        super(JanitorBot, self).send_message(chat_id=self.channel_id,
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


def telegram_remove_ip(bot, update, args):
	try:
		message(remove_ip(args[0]))
	except (IndexError, ValueError):
		update.message.reply_text("usage: /remove_ip <tag>")

def start():
	with open(CONFIG_FILE, encoding="utf-8") as f:
		config = json.load(f)
		token = config["token"]

	updater= Updater(token=token)
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler('add_ip', telegram_add_ip, pass_args=True))
	dispatcher.add_handler(CommandHandler('print_ips', telegram_print_ips))
	dispatcher.add_handler(CommandHandler('remove_ip', telegram_remove_ip, pass_args=True))

	with open(IP_FILE, encoding="utf-8") as f:
		data = json.load(f)
		if len(data["ips"])==0:
			message("there's no ip, can't ping it")
		for i in range(0, len(data["ips"])):
			Thread(target=pinging, args=(data["ips"][i]["address"],data["ips"][i]["tag"])).start()
		
	Thread(target=updater.start_polling).start()

if __name__ == "__main__":
	# Options
	parser = argparse.ArgumentParser(description="simple bot to monitor a local network")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("--add_ip", "-a", metavar=("ip_address","tag"), nargs=2,
	                    help="add an ip address with a tag. example: 192.168.1.1 router")
	group.add_argument("--config", "-c", action="store_true",
						help="set telegram params (token, channel_id)")
	group.add_argument("--message", "-m",
						help="send a message to the channel")
	group.add_argument("--print_ips", "-p", action="store_true",
						help="print saved ips")
	group.add_argument("--remove_ip", "-r", metavar="tag",
						help="remove ip identified with given tag.")
	group.add_argument("--start", "-s", action="store_true",
						help="start running the script")

	args = parser.parse_args()

	if args.add_ip:
		address = args.add_ip[0]
		tag = args.add_ip[1]
		add_ip(address,tag)
	if args.config:
		config()
	if args.message:
		message(args.message)
	if args.print_ips:
		print_ips()
	if args.remove_ip:
		remove_ip(args.remove_ip)
	if args.start:
		start()
