import database as DB
import cherrypy
from collections import defaultdict
import pickle

class Server:
		
	def registerAgent(self, agent):
		db = DB.Database()
		id = db.addAgent(agent)
		return str(id)
		
	def setProposal(self, word, explanation, agent_id):
		db = DB.Database()
		db.addProposal(word, explanation, agent_id)
		return word
		
	def ping(self):
		return "works"
		
	def setFeedback(self, agent_id, word_id, score, framing):
		db = DB.Database()
		ret = db.addScore(word_id, agent_id, score, framing)
		return ret
		
	def getMyFeedback(self, agent_id):
		db = DB.Database()
		feedback = db.getAgentFeedback(agent_id)
		return pickle.dumps(feedback)
		
	def getAllFeedback(self):
		db = DB.Database()
		feedback = db.getAllFeedback()
		return pickle.dumps(feedback)	
		
	def getUnscored(self, agent_id):
		db = DB.Database()
		words = db.getWords()
		scores = db.getScores()
		scoredict = defaultdict(set)
		for s in scores:
			scoredict[s[0]].add(s[1])
		unscored = list()
		word_attr = dict()
		for word in words:
			word = list(word)
			word[1:] = map(lambda x: str(x), word[1:])
			word_attr[word[0]] = [str(word[0])] + word[1:]
			if word[0] not in scoredict and word[-2] != agent_id:
				unscored.append(word)
		for key in scoredict:
			if agent_id not in scoredict[key] and word_attr[key][-2] != agent_id:
				unscored.append(word_attr[key])
		return pickle.dumps(unscored)
		
	registerAgent.exposed = True
	setProposal.exposed = True
	ping.exposed = True
	getUnscored.exposed = True
	getMyFeedback.exposed = True
	setFeedback.exposed = True
		
cherrypy.config.update({'server.socket_port' : 15000})		
cherrypy.quickstart(Server())