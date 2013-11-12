import time
import urllib
import urllib2
import csv
from operator import itemgetter
import pickle
import re

class Word:
	"""
    Word encapsulates a word. This is a more convenient way for accessing the 
    attributes of the word.
    """
	def __init__(self, word_id, word, timestamp, agent_id, explanation):
		self.word_id = word_id
		self.word = word
		self.timestamp = timestamp
		self.agent_id = agent_id
		self.explanation = explanation
		
class Feedback:
	"""
    Feedback encapsulates the information of a feedback. These attributes can be 
	used in adaption function.
    """
	def __init__(self, word_id, scoring_agent_id, word, timestamp, explanation, creator_agent_id, score, framing):
		self.word_id = word_id
		self.scoring_agent_id = scoring_agent_id
		self.word = word
		self.timestamp = timestamp
		self.explanation = explanation
		self.creator_agent_id = creator_agent_id
		self.score = score
		self.framing = framing

class Agent:

	"""
    Agent implements the basic functions of the agent, mainly the communication with the server. 
    The agent object implemented in this file is not capable of doing nothing but connecting to the server. 
    The object has interface functions score, adapt and generate. 
    """
    
	def __init__(self, name):
		"""
		Initializes the agent and connects it to the server. The agents are not meant to be
		running without connection to the environment server. 
		"""
		self.name = name
		self.hostname = "127.0.0.1"
		self.port = "15000"
		self.host = "http://" + self.hostname + ":" + self.port  + "/"
		# The goal of these parameters is to keep track, what were the last
		# words which were included from the server during the last call. As it 
		# does not make sense to ask for the same data all the time.
		self.wordId = 0
		self.wordScoreId = 0
		self.feedback = list()
		self.nameMapping = dict()
		self.start()
		
	def getUrl(self, query, param):
		"""
		getUrl implements the connection to the localhost server.
		"""
		url = "http://%s:%s/%s?%s" % (self.hostname, self.port, query, urllib.urlencode(param)) 
		html = urllib2.urlopen(url).read()
		return html
		
	def connectToServer(self):
		"""
		connectToServer is a function which pings the server and returns True if 
		it succesfully connected the server. False otherwise.
		"""
		html = self.getUrl("ping", {})
		if html == "works":
			return True
		else:
			return False
			
	def register(self):
		"""
		Registers the agents to the server. The agents are identified by the names.
		Do NOT start many agents with the same name, as it might lead to
		unexpected results.
		"""
		html = self.getUrl("registerAgent", {"agent" : self.name})
		self.id = html
		print "Registration to server successful"
		return self.id
		
	def lifeCycle(self):
		"""
		lifeCycle defines the method how the agent behaves in each step. Whether it
		scores a word/phrase, adapts to feedback or generates a new word/phrase.
		"""
		# Just an interface, not implemented
		return
		
	def score(self, word):
		"""
		score is a function which takes a string as an input and returns an evaluation
		of the this word. 
		"""
		# Just an interface, not implemented
		return
	
	def adapt(self, feedback):
		"""
		adapt is a function which takes a list of feedback as an input and adapts
		its parameters according to the feedback
		"""
		return
	
	def generate(self):
		# Just an interface, not implemented
		"""
		generate is a function which takes generates a phrase.
		"""
		return
		
	def propose(self, word, framing):
		# Connect server and send the proposal.
		"""
		propose takes the string word and framing information as input and sends this
		to the server.
		Disclaimer:
		If you want to address some attributes of the word in the framing information
		then the template you should follow is this:
		....I find the attribute <function_name> to be as <high/low/varying> as I....
		An example instance:
		I propose a phrase "Jane is cool" because I find the attribute Phrase Length 
		to be as high as I prefer. 

		The varying keyword is reserved for functions which analyse the phrase as a 
		list of words. For instance the vowel rate in words could be too varying.
		"""
		print "I am proposing a word: \"" + word + "\" because " + framing
		html = self.getUrl("setProposal", {"word" : word, "explanation" : framing, "agent_id": self.id})
		
	def getUnscoredWords(self):
		"""
		getUnscoredWords returns a set of words in the descending order of
		their proposal time.
		"""
		# Connect server and query for unrated words
		data = pickle.loads(self.getUrl("getUnscored", {"agent_id" : self.id}))
		dat = list()
		for spl in data:
			dat.append(Word(spl[0], spl[1], spl[2], spl[3], spl[4]))
		dat = sorted(dat, key=lambda x: x.timestamp, reverse=True)
		return dat
		
	def sendFeedback(self, word, score, framing, wordtext=""):
		"""
		sendFeedback takes the string word and framing information as input and sends this
		to the server.
		If you want to address some attributes of the word in the framing information
		then the template you should follow is this:
		....I find the attribute <function description> to be as <high/low/varying> as I....
		An example instance:
		I do not like the phrase "I didn't do it" by agent Smith because I find the attribute 
		Phrase Vowels to be too high and I find the attribute Phrase Consonants to be too low.
		"""
		# Connect server and send the feedback
		print "I am sending the feedback to word \"" + wordtext + "\" and the score is " + str(score) + " because " + framing
		html = self.getUrl("setFeedback", {"agent_id" : self.id, "word_id": word, "score": score, "framing": framing})
		
	def getAllFeedback(self):
		"""
		getAllFeedback is a function which returns all the feedback given to every phrase.
		"""
		print "I want to know what the general population thinks of different phrases"
		p = pickle.loads(self.getUrl("getAllFeedback", {"rowId" : self.wordId}))
		for pl in p:
			self.feedback.append(Feedback(pl[0], pl[1], pl[2], pl[3], pl[4], pl[5], pl[6], pl[7]))
			self.wordId = max(self.wordId, pl[8])
		return self.feedback
				
	def submitAttribute(self, attributeName, attributeFuncton, attributeString, agent_id=-1):
		"""
		This functions sends the attribute to the server for other agents to use.
		"""
		if agent_id == -1:
			return
		else:
			#attributeName, attributeFuncton, attributeString, agent_id
			self.getUrl("addAttribute", {"attributeName" : attributeName, "attributeFuncton" : attributeFuncton, "attributeString" : attributeString, "agent_id" : agent_id})
		
	def getFramingAttributes(self, feedback):
		"""
		getFramingAttributes is a function which returns all the feedback given to every phrase.
		"""
		#I find the attribute <function description> to be as <high/low/varying>
		pattern = re.compile("I find the attribute (.+?) to be too (high|low|varying)")
		return pattern.findall(feedback.framing)
		
	def getAttribute(self, attributeName, agent_id):
		"""
		This functions asks for the attribute from the server and loads it for 
		the agent object. The function returns the natural language represantation
		of the function.
		"""
		# function_name string, name string, agent_id string, function string
		dat = pickle.loads(self.getUrl("getAttribute", {"attributeName" : attributeName, "agent_id" : agent_id}))
		if dat is not None:
			self.loadAttribute(dat[3], dat[1], dat[0], dat[2])
			return dat[1]
		
		
	def callFunction(self, function, parameter):
		"""
		This function is used for calling the different attribute function
		loaded from the attributes.py file or from the server
		"""
		return self.ns[function](parameter)
		
	#
	# The function is the source code
	# The function name is the natural language 'name' of the function (as in name in attributes.py)
	# The functionString is the function name as in source code
	def loadAttribute(self, function, functionName, functionString, agent_id=-1):
		code_local = compile(function, '<string>', 'exec')
		exec code_local in self.ns
		self.nameMapping[functionName] = functionString
		
	def parseFraming(self, feedback):
		"""
		This functions parses the attributes framing information from the feedback 
		object. The function returns a list of list. Each listitem is one attribute, found
		from the feedback and contains the following information:
		[the word, the callable function name, the natural language representation of the
		function, the valuation in the framing information (i.e. high, low, varying),
		the value of this attribute for the word]
		"""
		attributes = self.getFramingAttributes(feedback)
		parsed = list()
		for attribute in attributes:
			try:
				value = self.callFunction(self.nameMapping[attribute[0]], feedback.word)
			except:
				a = self.getAttribute(attribute[0], feedback.scoring_agent_id)
				value = self.callFunction(a, feedback.word)
			if value is not None:
				# This returns the list of lists. Each listitem is:
				# the word, the callable function name, natural language representation, in the framing
				# information whether its high or low, the value of the attribute for given phrase
				parsed.append([feedback.word, self.nameMapping[attribute[0]], attribute[0], attribute[1], value])
		return parsed
			
		
	def loadAttributes(self):
		"""
		This functions parses the attributes file. The goal of the attributes file
		is to define a set of functions, which take the phrase as input and return the
		value of the attribute for the respective phrase. Please look at some of the examples
		implemented in the attributes . 
		Also, these attributes are sent to the server, so if they are referred to by the
		attribute name in the framing information, the other agent can use them.
		"""
		f = open("attributes.py")
		dat = f.read()
		f.close()
		attributes = re.findall("\<attribute\>(.+?)\<\/attribute\>", dat, re.DOTALL)
		self.ns = {}
		for attribute in attributes:
			name = re.findall("\<name\>(.+?)\<\/name\>", attribute, re.DOTALL)[0].strip()
			isStandard = False
			if("(standard)" in name):
				name = name.replace("(standard)", "")
				isStandard = True
			else:
				name += " (" + self.name + ")"
			name = name.strip().lower()
			function = re.findall("\<function\>(.+?)\<\/function\>", attribute, re.DOTALL)[0]
			functionName = re.findall("def (.+?)\(", function)[0]
			if not isStandard:
				functionName = self.name + "_" + functionName
				function = re.sub("def (.+?)\(", "def " + self.name + "_\g<1>(", function)
				self.submitAttribute(name, function, functionName, self.id)
			self.loadAttribute(function, name, functionName)
		
	def start(self):
		"""
		This function connects the agent to the server and starts the endless cycle 
		of actions.
		"""
		if self.connectToServer():
			self.id = self.register()
			self.loadAttributes()
			while(True):
				self.lifeCycle()
		else:
			print "I am agent named " + self.name + " and I was not able to connect to the server. Please help!"