import sqlite3
from collections import defaultdict
import hashlib
import time

class Database:

	# The constant if agent already exists
	AGENT_EXISTS = -1
	SCORE_EXISTS = -1
	SELF_SCORING = -2
	
	def __init__(self):
		self.db = sqlite3.connect("gamestate.sqlite")
		self.db.execute("CREATE TABLE IF NOT EXISTS agent(rowid INTEGER primary key AUTOINCREMENT, id string , name string)")
		self.db.execute("CREATE TABLE IF NOT EXISTS word(rowid INTEGER primary key AUTOINCREMENT, id string , word string, timestamp timestamp DEFAULT NOW, agent_id string, explanation string)")
		self.db.execute("CREATE TABLE IF NOT EXISTS word_score(rowid INTEGER primary key AUTOINCREMENT, word_id string, agent_id string, score float, framing string, timestamp timestamp DEFAULT NOW)")
		self.db.execute("CREATE TABLE IF NOT EXISTS attribute(natural_language_representation string, name string, agent_id string, function string)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_1 ON agent(id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_2 ON word(id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_4 ON word(agent_id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_5 ON attribute(agent_id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_6 ON attribute(name, agent_id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_7 ON word(rowid)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_8 ON word_score(rowid, word_id, agent_id)")
		
	def addAttribute(self, attributeName, attributeFuncton, attributeString, agent_id):
		cursor = self.db.execute("INSERT INTO attribute(natural_language_representation, function, name, agent_id) VALUES(?, ?, ?, ?)", [attributeName, attributeFuncton, attributeString, agent_id])
		self.db.commit()
		
	def getAllAttributes(self, attributeName, agent_id):
		cursor = self.db.execute("SELECT * FROM attribute")
		result = cursor.fetchall()
		return result
			
	def addAgent(self, agent):
		cursor = self.db.execute("SELECT id, name FROM agent WHERE id=?", [hashlib.md5(agent).hexdigest()])
		result = cursor.fetchall()
		if len(result) > 0:
			return result[0][0]
		else:
			self.db.execute("INSERT INTO agent(id, name) VALUES(?, ?)", [hashlib.md5(agent).hexdigest(), agent])
			self.db.commit()
			return hashlib.md5(agent).hexdigest()
			
	def getAttribute(self, attributeName, agent_id):
		print attributeName, agent_id
		cursor = self.db.execute("SELECT * FROM attribute WHERE natural_language_representation = ? AND agent_id = ?", [attributeName, agent_id])
		result = cursor.fetchall()
		if len(result) > 0:
			return result[0]
		else:
			return None
			
	def addProposal(self, word, explanation, agent_id):
		t = time.time()
		try:
			self.db.execute("INSERT INTO word(id, word, explanation, timestamp, agent_id) VALUES(?, ?, ?, ?, ?)", [hashlib.md5(word + explanation + str(t)).hexdigest(), word, explanation, t, agent_id])
			self.db.commit()
		except sqlite3.IntegrityError as e:
			return -1
		return 1

	def addScore(self, word_id, agent_id, score, framing):
		cursor = self.db.execute("SELECT agent_id FROM word WHERE id=?", [word_id])
		result = cursor.fetchall()
		if result[0][0] == agent_id:
			return str(self.SELF_SCORING)
		cursor = self.db.execute("SELECT word_id, agent_id, score, framing, timestamp FROM word_score WHERE word_id=? and agent_id=?", [word_id, agent_id])
		result = cursor.fetchall()
		if len(result) > 0:
			return str(self.SCORE_EXISTS)
		else:
			cursor = self.db.execute("INSERT INTO word_score(word_id, agent_id, score,framing) VALUES(?, ?, ?, ?)", [word_id, agent_id, score, framing])
			self.db.commit()
			return "1"
		
	def getAllFeedback(self, rowId):
		cursor = self.db.execute("SELECT word_score.word_id, word_score.agent_id, word.word, word.timestamp, word.explanation, word.agent_id, word_score.score, word_score.framing, word_score.rowId FROM word_score LEFT JOIN word ON word_id=word.id WHERE  word_score.rowid > ?", [rowId])
		scores = cursor.fetchall()
		return scores
			
	def getWords(self):
		cursor = self.db.execute("SELECT id , word, timestamp, agent_id, explanation  FROM word")
		words = cursor.fetchall()
		return words
			
	def getScores(self):
		cursor = self.db.execute("SELECT word_score.word_id, word_score.agent_id, word.word, word.timestamp, word.explanation, word.agent_id FROM word_score LEFT JOIN word ON word_id = word.id")
		scores = cursor.fetchall()
		return scores

	def getAgents(self):
		cursor = self.db.execute("SELECT id FROM agent")
		agents = cursor.fetchall()
		return agents