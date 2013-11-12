import agent
import random
import time
from agent import Feedback

class VowelAgent(agent.Agent):
	"""
    VowelAgent implements a sample functional agent.
    """
	def __init__(self, name):
		# Anything you want to initialize
		self.vowelWeight = random.random()
		self.consonantWeight = random.random()
		self.generateVowel = 0.5
		agent.Agent.__init__(self, name)
		
	def lifeCycle(self):
		"""
		The function which is repeatedly started and defines the behaviour
		of the agent in the context of adaption, scoring and generating.
		"""
		r = random.random()
		feedback = Feedback("1", "62eb49e12fab557391bdd844a9efdd84", 'I didn\'t do it', "", 'This is the explanation by the creator', "", 0.5, 'I do not like the phrase "I didn\'t do it" by agent Smith because I find the attribute string length (teamname_agentasd) to be too high and I find the attribute string length (teamname_agentasd) to be too low')
		fr = self.parseFraming(feedback)
		self.callFunction("strLen", "Common sense is not so common")
		if r < 0.33:
			self.generate()
		if r > 0.33 and r < 0.66:
			## Gives the lists of lists, where each sublist is, ordered by timestamp desc:
			## [Word, Word], see documentation
			unratedwords = self.getUnscoredWords()
			if len(unratedwords) > 0:
				scr = self.score(unratedwords[0].word)
				framing = "This is not a nice word"
				self.sendFeedback(unratedwords[0].word_id, scr, framing, wordtext=unratedwords[0].word)
		elif r > 0.66:
			## The result is the following:
			## [Feedback, Feedback], see documentation
			feedback = self.getAllFeedback()
			self.adapt(feedback)
			
		#time.sleep(1)
		
	def score(self, word):
		"""
		score implements a sample function which gives a score to a word. In this case
		it the score is calculated such, that the word has a desired fraction of
		consonants and vowels.
		"""
		vowels = 0.0
		consonants = 0.0
		vowelstr = "aeiou"
		for letter in word:
			if letter in vowelstr:
				vowels += 1
			else:
				consonants += 1
		total = vowels + consonants
		scr = 1 - abs(self.vowelWeight - (vowels/total)) - abs(self.consonantWeight - (consonants/total))
		return scr
		
	def generate(self):
		"""
		generate implements a sample function which generates a word with random
		length. The system makes a distinction between consonants and vowels and generates
		words by using a self.generateVowel variable, which adapts to the feedback.
		"""
		strlen = random.randint(1,10)
		word = ""
		vowels = "aeiou"
		consonants = "bcdfghjklmnpqrstvxyz"
		for i in range(strlen):
			r = random.random()
			if r < self.generateVowel:
				word += vowels[random.randint(0,len(vowels)-1)]
			else:
				word += consonants[random.randint(0,len(consonants)-1)]
		explanation = "I find the attribute phrase vowels to be as high as I prefer"
		## If the word is ready, propose it to the server
		self.propose(word, explanation)
		
	def adapt(self, feedback):
		"""
		adapt implements a sample function which changes the self.generateVowel
		according to the feedback of other agents.
		"""
		vowelsCount = 0.0
		consCount = 0.0
		vowels = "aeiou"
		consonants = "bcdfghjklmnpqrstvxyz"
		for f in feedback:
			for c in f.word:
				if c in vowels:
					vowelsCount += 1*f.score
				else:
					consCount += 1*f.score
		if vowelsCount + consCount != 0:
			self.generateVowel = vowelsCount/(vowelsCount + consCount)
		print "I generate vowels with frequency " + str(self.generateVowel)