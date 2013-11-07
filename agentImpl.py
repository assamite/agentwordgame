import agent
import random
import time

class AgentImpl(agent.Agent):

	def __init__(self, name):
		# Anything you want to initialize
		agent.Agent.__init__(self, name)
		
	def lifeCycle(self):
		r = random.random()
		if r < 0.33:
			self.generate()
		if r > 0.33 and r < 0.66:
			## Gives the lists of lists, where each sublist is, ordered by timestamp desc:
			## [UnscoredWord, UnscoredWord], see documentation
			unratedwords = self.getUnscoredWords()
			if len(unratedwords) > 0:
				scr = self.score(unratedwords[0].word)
				self.sendFeedback(unratedwords[0].word_id, scr, wordtext=unratedwords[0].word)
				
		elif r > 0.66:
			## The result is the following:
			## [MyFeedback, MyFeedback], see documentation
			feedback = self.getMyFeedback()
			self.adapt(feedback)
			
		#time.sleep(1)
		
	def score(self, word):
		vowels = 0.0
		consonants = 0.0
		vowelstr = "aeiou"
		for letter in word:
			if letter in vowelstr:
				vowels += 1
			else:
				consonants += 1
		scr = vowels/(vowels+consonants)
		return scr
		
	def generate(self):
		strlen = random.randint(1,10)
		word = ""
		for i in range(strlen):
			alphabet = "abcdefghijklmnopqrstuvxyz"
			r = random.randint(0, len(alphabet)-1)
			word += alphabet[r]
		explanation = "I have no idea why this is a good word. I generated this randomly"
		## If the word is ready, propose it to the server
		self.propose(word, explanation)
		
	def adapt(self, feedback):
		return