import time
import urllib
import urllib2
import csv
from operator import itemgetter
import pickle
import re

class UnscoredWord:

	def __init__(self, word_id, word, timestamp, agent_id, explanation):
		self.word_id = word_id
		self.word = word
		self.timestamp = timestamp
		self.agent_id = agent_id
		self.explanation = explanation
		
class MyFeedback:

	def __init__(self, word_id, scoring_agent_id, word, timestamp, explanation, creator_agent_id, score):
		self.word_id = word_id
		self.scoring_agent_id = scoring_agent_id
		self.word = word
		self.timestamp = timestamp
		self.explanation = explanation
		self.creator_agent_id = creator_agent_id
		self.score = score

class Agent:

	def __init__(self, name):
		self.name = name
		self.host = "http://http://127.0.0.1:15000/"
		self.start()
		
	def getUrl(self, query, param):
		port = "15000"
		url = "http://localhost:%s/%s?%s" % (port, query, urllib.urlencode(param)) 
		html = urllib2.urlopen(url).read()
		return html
		
	def connectToServer(self):
		html = self.getUrl("ping", {})
		if html == "works":
			return True
		else:
			return False
			
	def register(self):
		html = self.getUrl("registerAgent", {"agent" : self.name})
		self.id = html
		print "Registration to server successful"
		return self.id
		
	def lifeCycle(self):
		# Just an interface, not implemented
		return
		
	def score(self, word):
	# Just an interface, not implemented
	return
	
	def adapt(self):
	# Just an interface, not implemented
	return
	
	def generate(self):
	# Just an interface, not implemented
	return
		
	def propose(self, word, explanation):
		# Connect server and send the proposal.
		print "I am proposing a word: \"" + word + "\" because " + explanation
		html = self.getUrl("setProposal", {"word" : word, "explanation" : explanation, "agent_id": self.id})
		
	def getUnscoredWords(self):
		# Connect server and query for unrated words
		data = pickle.loads(self.getUrl("getUnscored", {"agent_id" : self.id}))
		for spl in data:
			dat.append(UnscoredWord(spl[0], spl[1], spl[2], spl[3], spl[4]))
		dat = sorted(dat, key=lambda x: x.timestamp, reverse=True)
		return dat
		
	def sendFeedback(self, word, score, wordtext=""):
		# Connect server and send the feedback
		print "I am sending the feedback to word \"" + wordtext + "\" and the score is " + str(score)
		html = self.getUrl("setFeedback", {"agent_id" : self.id, "word_id": word, "score": score})
		
	def getMyFeedback(self):
		print "I want to know what others think of my words"
		p = pickle.loads(self.getUrl("getMyFeedback", {"agent_id" : self.id}))
		feedback = list()
		for pl in p:
			feedback.append(MyFeedback(pl[0], pl[1], pl[2], pl[3], pl[4], pl[5], pl[6]))
		feedback = sorted(feedback, key=lambda x: x.timestamp, reverse=True)
		return feedback
		
	def loadAttributes(self):
		f = open("attributes.py")
		dat = f.read()
		f.close()
		attributes = re.findall("\<attribute\>(.+?)\<\/attribute\>", dat, re.DOTALL)
		for attribute in attributes:
			name = re.findall("\<name\>(.+?)\<\/name\>", attribute, re.DOTALL)
			function = re.findall("\<function\>(.+?)\<\/function\>", attribute, re.DOTALL)[0]
			functionName = re.findall("def (.+?)\(", function)
			exec(function[0])
			print functionName
		print phraseConsonants("asoifsaoih asoi hfoaish sa")
		
	def start(self):
		self.loadAttributes()
		exit()
		if self.connectToServer():
			self.register()
			while(True):
				self.lifeCycle()
		else:
			print "I am agent named " + self.name + " and I was not able to connect to the server. Please help!"