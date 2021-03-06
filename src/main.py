#!/usr/bin/python3

import os
import logging.handlers
import time
import sys
import signal
import traceback

import globals
import reddit
import messages
import database
import wiki
import utils
import state
import sheets

### Logging setup ###
LOG_LEVEL = logging.DEBUG
if not os.path.exists(globals.LOG_FOLDER_NAME):
	os.makedirs(globals.LOG_FOLDER_NAME)
LOG_FILENAME = globals.LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256 * 16


class ContextFilter(logging.Filter):
	def filter(self, record):
		record.gameid = globals.logGameId
		return True


log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(gameid)s %(message)s')
log_stdHandler = logging.StreamHandler()
log_stdHandler.setFormatter(log_formatter)
log.addHandler(log_stdHandler)
log.addFilter(ContextFilter())
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
	log_fileHandler.setFormatter(log_formatter)
	log.addHandler(log_fileHandler)


def signal_handler(signal, frame):
	log.info("Handling interupt")
	database.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


log.debug("Connecting to reddit")

once = False
debug = False
user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]
	for arg in sys.argv:
		if arg == 'once':
			once = True
		elif arg == 'debug':
			debug = True
else:
	log.error("No user specified, aborting")
	sys.exit(0)


if not reddit.init(user):
	sys.exit(0)

database.init()

wiki.loadPages()

while True:
	try:
		for message in reddit.getMessageStream():
			startTime = time.perf_counter()
			log.debug("Processing message")
			wiki.loadPages()

			try:
				messages.processMessage(message)
			except Exception as err:
				log.warning("Error in main loop")
				log.warning(traceback.format_exc())
				if globals.gameId is not None:
					log.debug("Setting game {} as errored".format(globals.gameId))
					database.setGameErrored(globals.gameId)
					ownerMessage = "[Game]({}) errored. Click [here]({}) to clear."\
						.format("{}{}".format(globals.SUBREDDIT_LINK, globals.logGameId[1:-1]),
					            utils.buildMessageLink(
			                        globals.ACCOUNT_NAME,
			                        "Kick game",
			                        "kick {}".format(globals.gameId)
			                    ))
				else:
					ownerMessage = "Unable to process message from /u/{}, skipping".format(str(message.author))

				try:
					reddit.sendMessage(globals.OWNER, "NCFAA game errored", ownerMessage)
					message.mark_read()
				except Exception as err2:
					log.warning("Error sending error message")
					log.warning(traceback.format_exc())

			for threadId in database.getGamesPastPlayclock():
				techFoul = True
				log.debug("Game past playclock: {}".format(threadId))
				game = utils.getGameByThread(threadId)
				if not game['tip']['homeTip'] and not game['tip']['awayTip'] and game['waitingAction'] == 'tip':
					game['away']['playclockPenalties'] += 1
					game['home']['playclockPenalties'] += 1
					techFoul = False
					penaltyMessage = "You two souls both got a DOG at the same time. Please send your tip message."
				elif not game['tip']['homeTip'] and game['tip']['awayTip'] and game['waitingAction'] == 'tip':
					game['home']['playclockPenalties'] += 1
					game['waitingOn'] = 'home'
					game['status']['possession'] = 'away'
				elif game['tip']['homeTip'] and not game['tip']['awayTip'] and game['waitingAction'] == 'tip':
					game['away']['playclockPenalties'] += 1
					game['waitingOn'] = 'away'
					game['status']['possession'] = 'home'
				else:
					game[game['waitingOn']]['playclockPenalties'] += 1
					penaltyMessage = "{} has not sent their number in over {} hours, playclock penalty. This is their {} penalty.".format(
					utils.getCoachString(game, game['waitingOn']),globals.delayHours, utils.getNthWord(game[game['waitingOn']]['playclockPenalties']))
				if game['home']['playclockPenalties'] == 3 and game['away']['playclockPenalties'] == 3:
					## This needs to be where we do something if both players hit 3
					utils.endGameBothDelay(game,threadId)
				elif game[game['waitingOn']]['playclockPenalties'] >= 3:
					log.debug("3 penalties, game over")
					game['status']['halfType'] = 'end'
					game['waitingAction'] = 'end'
					resultMessage = "They forfeit the game. {} has won!".format(utils.flair(game[utils.reverseHomeAway(game['waitingOn'])]))
					utils.endGameDelayOfGame(game, threadId)


				elif techFoul:
					state.technicalFouls(game)
				else:
					utils.sendGameComment(game, penaltyMessage, {'action': 'death'})
					pass

				database.setGamePlayed(game['dataID'])
				utils.updateGameThread(game)

			log.debug("Message processed after: %d", int(time.perf_counter() - startTime))
			utils.clearLogGameID()
			if once:
				database.close()
				break

	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	if once:
		break

	time.sleep(5 * 60)
