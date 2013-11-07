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
		self.db.execute("CREATE TABLE IF NOT EXISTS agent(id string primary key, name string)")
		self.db.execute("CREATE TABLE IF NOT EXISTS word(id string primary key, word string, timestamp timestamp DEFAULT NOW, agent_id string, explanation string)")
		self.db.execute("CREATE TABLE IF NOT EXISTS word_score(word_id string, agent_id string, score float,timestamp timestamp DEFAULT NOW)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_1 ON agent(id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_2 ON word(id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_3 ON word_score(word_id, agent_id)")
		self.db.execute("CREATE INDEX IF NOT EXISTS idx_4 ON word(agent_id)")
			
	def addAgent(self, agent):
		cursor = self.db.execute("SELECT * FROM agent WHERE id=?", [hashlib.md5(agent).hexdigest()])
		result = cursor.fetchall()
		if len(result) > 0:
			return result[0][0]
		else:
			self.db.execute("INSERT INTO agent(id, name) VALUES(?, ?)", [hashlib.md5(agent).hexdigest(), agent])
			self.db.commit()
			return hashlib.md5(agent).hexdigest()
			
	def addProposal(self, word, explanation, agent_id):
		t = time.time()
		try:
			self.db.execute("INSERT INTO word(id, word, explanation, timestamp, agent_id) VALUES(?, ?, ?, ?, ?)", [hashlib.md5(word + explanation + str(t)).hexdigest(), word, explanation, t, agent_id])
			self.db.commit()
		except sqlite3.IntegrityError as e:
			return -1
		return 1

	def addScore(self, word_id, agent_id, score):
		cursor = self.db.execute("SELECT agent_id FROM word WHERE id=?", [word_id])
		result = cursor.fetchall()
		if result[0][0] == agent_id:
			return str(self.SELF_SCORING)
		cursor = self.db.execute("SELECT * FROM word_score WHERE word_id=? and agent_id=?", [word_id, agent_id])
		result = cursor.fetchall()
		if len(result) > 0:
			return str(self.SCORE_EXISTS)
		else:
			cursor = self.db.execute("INSERT INTO word_score(word_id, agent_id, score) VALUES(?, ?, ?)", [word_id, agent_id, score])
			self.db.commit()
			return "1"
			
	def getAgentFeedback(self, agent_id):
		cursor = self.db.execute("SELECT word_score.word_id, word_score.agent_id, word.word, word.timestamp, word.explanation, word.agent_id, word_score.score FROM word_score LEFT JOIN word ON word_id=word.id WHERE word.agent_id=?", [agent_id])
		scores = cursor.fetchall()
		return scores
			
	def getWords(self):
		cursor = self.db.execute("SELECT * FROM word")
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