import sqlite3
from datetime import datetime

import globals

dbConn = None


def init():
	global dbConn
#	dbConn = sqlite3.connect(globals.DATABASE_NAME)

	dbConn = sqlite3.connect(globals.DATABASE_NAME)
	c = dbConn.cursor()
	c.execute('''
		CREATE TABLE IF NOT EXISTS games (
			ID INTEGER PRIMARY KEY AUTOINCREMENT,
			ThreadID VARCHAR(80) NOT NULL,
			DefenseNumber INTEGER,
			homeTip INTEGER,
			awayTip INTEGER,
			Deadline TIMESTAMP NOT NULL DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+10 days')),
			Playclock TIMESTAMP NOT NULL DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+24 hours')),
			Complete BOOLEAN NOT NULL DEFAULT 0,
			Errored BOOLEAN NOT NULL DEFAULT 0,
			UNIQUE (ThreadID)
		)
	''')
	c.execute('''
		CREATE TABLE IF NOT EXISTS coaches (
			ID INTEGER PRIMARY KEY AUTOINCREMENT,
			GameID INTEGER NOT NULL,
			Coach VARCHAR(80) NOT NULL,
			HomeTeam BOOLEAN NOT NULL,
			UNIQUE (Coach, GameID),
			FOREIGN KEY(GameID) REFERENCES games(ID)
		)
	''')
	c.execute('''
		CREATE TABLE IF NOT EXISTS plays (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		GameID INTEGER NOT NULL,
		OffCoach VARCHAR(80) NOT NULL,
		DefCoach VARCHAR(80) NOT NULL,
		Playtype char(10),
		Call char(30),
		ONum INTEGER NOT NULL,
		DNum INTEGER NOT NULL,
		Diff INTEGER NOT NULL,
		Result char(20),
		Quarter int,
		Playclock char(6),
		FOREIGN KEY(GameID) REFERENCES games(ID)
		)
	''')
	c.execute('''
		CREATE TABLE IF NOT EXISTS stats (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		GameID INTEGER NOT NULL,
		Team Char(35),
		Points int,
		PointsAgainst int,
		Mov int,
		ShotsTaken int,
		ShotsMade int,
		ThreesTaken int,
		ThreesMade int,
		FreesTaken int,
		FreesMade int,
		Turnovers int,
		TurnoversForced int,
		Steals int,
		Blocks int,
		OffReb int,
		DefReb int,
		FoulsCommitted int,
		TimesFouled int,
		Top char(5),
		Win int,
		possessionsFor int,
		OffDiffAve float,
		DefDiffAve float,
		TotShotsAgainst int,
		TotMadeAgainst int,
		ThreesTakenAgainst int,
		ThreesMadeAgainst int,
		FreesTakenAgainst int,
		FreesMadeAgainst int,
		StealsAgainst int,
		BlocksAgainst int,
		TopAgainst int,
		possessionsAgainst int,
		Proccessed char(1),
		FOREIGN KEY(GameID) REFERENCES games(ID)

		)


	''')

	c.execute('''
	CREATE TABLE IF NOT EXISTS Week
	(week char(10))
	''')

	c.execute(''' CREATE TABLE IF NOT EXISTS chewers
	   (Rname char(50))  ''')
	dbConn.commit()



def close():
	dbConn.commit()
	dbConn.close()


def checkInChewers(name):
	c = dbConn.cursor()
	try:
		c.execute('''
		select count(*) from chewers where Rname = ?
		''',(name,))
	except sqlite3.IntegrityError:
		return false
	if c.rowcount > 0:
		return True
	else:
		return False
def getWeek():
	c = dbConn.cursor()
	try:
		c.execute('''
		select week from weeks
		''')
	except sqlite3.IntegrityError:
		return False
	result = c.fetchone()
	return result[0]


def insertStats(stats):
	c = dbConn.cursor()
	try:
		c.execute('''INSERT INTO stats(GameID, Team, Points, PointsAgainst, Mov, ShotsTaken, ShotsMade, ThreesTaken, ThreesMade, \
		FreesTaken, FreesMade, Turnovers, TurnoversForced, Steals, Blocks, OffReb, DefReb, FoulsCommitted,\
                TimesFouled, Top, Win, OffDiffAve, DefDiffAve, TotShotsAgainst, TotMadeAgainst, ThreesTakenAgainst,\
                ThreesMadeAgainst, FreesTakenAgainst, FreesMadeAgainst, StealsAgainst, BlocksAgainst, TopAgainst, Proccessed, possessionsFor, possessionsAgainst)
                Values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (stats['dataID'], stats['name'], stats['scored'], stats['scoredAgainst'],
				stats['mov'], stats['totShots'], stats['totMade'], stats['3PtAttempted'], stats['3PtMade'], stats['FTAttempted'], stats['FTMade'], stats['turnovers'],
				stats['turnoversGained'], stats['steals'], stats['blocks'], stats['offRebound'], stats['defRebound'], stats['fouls'], stats['timesFouled'],
				stats['posTime'], stats['win'], stats['offDiffAve'], stats['defDiffAve'], stats['totShotsAgainst'], stats['totMadeAgainst'], stats['3PtAttemptedAgainst'],
				stats['3PtMadeAgainst'], stats['FTAttemptedAgainst'], stats['FTMadeAgainst'], stats['stealsAgainst'], stats['blocksAgainst'], stats['posTimeAgainst'],0,
				stats['possessions'], stats['possessionsAgainst']) )
	except sqlite3.IntegrityError:
		return False
	dbConn.commit()
	if c.rowcount == 1:
		return True
	else:
		return False




def insertNewPlays(gameid, ocoach, dcoach, ptype, call, onum, dnum, diff, result, qrt, pclock):

	c = dbConn.cursor()
	try:
		c.execute('''insert into plays(GameID ,OffCoach ,DefCoach ,Playtype ,Call ,ONum ,Dnum ,Diff , Result, quarter, playclock)\
	values(?,?,?,?,?,?,?,?,?,?,?)''',(gameid ,ocoach ,dcoach ,ptype ,call ,onum ,dnum ,diff ,result, qrt, pclock))
		print ("should be inserted")

	except sqlite3.IntegrityError:
		return False
	dbConn.commit()
	return c.lastrowid


def createNewGame(thread):
	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO games
			(ThreadID)
			VALUES (?)
		''', (thread,))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()

	return c.lastrowid


def addCoach(gameId, coach, home):
	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO coaches
			(GameID, Coach, HomeTeam)
			VALUES (?, ?, ?)
		''', (gameId, coach.lower(), home))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()
	return True


def getTipById(ID,type_):
	c = dbConn.cursor()
	execString = '''
		SELECT {}
		FROM games
		WHERE ID = {}
	'''.format(type_, ID,)
	result = c.execute(execString)
	return result.fetchone()[0]


def saveTipNumber(gameID, number,type_):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET {} = {}
		WHERE ID = {}
	'''.format(type_, int(number), gameID,))
	dbConn.commit()
	return True

def nullTipNumbers(gameID):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET 'awayTip' = NULL, 'homeTip' = NULL
		where ID = {}
	'''.format(gameID))
	dbConn.commit()
	return True

def getGameByCoach(coach):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT g.ID
			,g.ThreadID
			,g.DefenseNumber
			,g.Errored
			,group_concat(c2.Coach) as Coaches
		FROM games g
			INNER JOIN coaches c
				ON g.ID = c.GameID
			LEFT JOIN coaches c2
				on g.ID = c2.GameID
		WHERE c.Coach = ?
			and g.Complete = 0
		GROUP BY g.ID, g.ThreadID, g.DefenseNumber
	''', (coach.lower(),))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None
	else:
		return {"id": resultTuple[0], "thread": resultTuple[1], "defenseNumber": resultTuple[2], "errored": resultTuple[3],
		        "coaches": resultTuple[4].split(',')}


def getGameByID(id):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT g.ThreadID
			,g.DefenseNumber
			,g.Errored
			,group_concat(c.Coach) as Coaches
		FROM games g
			LEFT JOIN coaches c
				ON g.ID = c.GameID
		WHERE g.ID = ?
			and g.Complete = 0
		GROUP BY g.ThreadID, g.DefenseNumber
	''', (id,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None
	else:
		return {"id": id, "thread": resultTuple[0], "defenseNumber": resultTuple[1], "errored": resultTuple[2],
		        "coaches": resultTuple[3].split(',')}


def endGame(threadId):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Complete = 1
			,Playclock = CURRENT_TIMESTAMP
		WHERE ThreadID = ?
	''', (threadId,))
	dbConn.commit()

	if c.rowcount == 1:
		return True
	else:
		return False


def saveDefensiveNumber(gameID, number):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Playclock = DATETIME(CURRENT_TIMESTAMP, '+24 hours')
			,DefenseNumber = ?
		WHERE ID = ?
	''', (number, gameID))
	dbConn.commit()


def getDefensiveNumber(gameID):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT DefenseNumber
		FROM games
		WHERE ID = ?
	''', (gameID,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None

	return resultTuple[0]


def clearDefensiveNumber(gameID):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Playclock = DATETIME(CURRENT_TIMESTAMP, '+24 hours')
			,DefenseNumber = NULL
		WHERE ID = ?
	''', (gameID,))
	dbConn.commit()


def pauseGame(threadID, hours):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Playclock = DATETIME(CURRENT_TIMESTAMP, '+' || ? || ' hours')
			,Deadline = DATETIME(Deadline, '+' || ? || ' hours')
		WHERE ThreadID = ?
	''', (str(hours), str(hours), threadID))
	dbConn.commit()


def setGamePlayed(gameID):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Playclock = DATETIME(CURRENT_TIMESTAMP, '+24 hours')
		WHERE ID = ?
	''', (gameID,))
	dbConn.commit()


def getGamePlayed(gameID):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT Playclock
		FROM games
		WHERE ID = ?
	''', (gameID,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None

	return datetime.strptime(resultTuple[0], "%Y-%m-%d %H:%M:%S")


def getGameDeadline(gameID):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT Deadline
		FROM games
		WHERE ID = ?
	''', (gameID,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None

	return datetime.strptime(resultTuple[0], "%Y-%m-%d %H:%M:%S")


def getGamesPastPlayclock():
	c = dbConn.cursor()
	results = []
	for row in c.execute('''
		SELECT ThreadID
		FROM games
		WHERE Playclock < CURRENT_TIMESTAMP
			and Complete = 0
			and Errored = 0
		'''):
		results.append(row[0])

	return results


def clearGameErrored(gameID):
	try:
		c = dbConn.cursor()
		c.execute('''
			UPDATE games
			SET Errored = 0
				,Deadline = DATETIME(Deadline, '+' || (julianday(CURRENT_TIMESTAMP) - julianday(Playclock) * 86400.0) || ' seconds')
				,Playclock = DATETIME(CURRENT_TIMESTAMP, '+24 hours')
			WHERE ID = ?
		''', (gameID,))
		dbConn.commit()
	except Exception as err:
		return False
	return True


def clearGameErroredOnly(gameID):
	execString = "update games set errored = 0 where ID = {}".format(gameID)

	try:
		c = dbConn.cursor()
		c.execute(execString)
		dbConn.commit()
	except Exception as err:
		return False
	return True


def setGameErrored(gameID):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Errored = 1
			,Playclock = CURRENT_TIMESTAMP
		WHERE ID = ?
	''', (gameID,))
	dbConn.commit()
