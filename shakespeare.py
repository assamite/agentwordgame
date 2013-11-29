import os

import agent
import random
import time
from agent import Feedback

class shakespeareAgent(agent.Agent):
	""" 'Shakespearean' insult generator. Just for fun. Does not really do 
	any computation or learning but generates insult noun phrases.
    """
	def __init__(self, name, insults_file = os.path.join(os.path.dirname(__file__), "insults.txt")):
		# Anything you want to initialize
		self.all_words = []
		self.insults_file = insults_file
		self.insults = self.read_insults()
		self.vowelWeight = random.random()
		self.consonantWeight = random.random()
		self.generateVowel = 0.5
		agent.Agent.__init__(self, name)
		
	def lifeCycle(self):
		"""
		The function which is repeatedly started and defines the behaviour
		of the agent in the context of adaption, scoring and generating.
		"""

		self.generate()

		time.sleep(1)
		
	def score(self, word):
		"""
		score implements a sample function which gives a score to a word. In this case
		it the score is calculated such, that the word has a desired fraction of
		consonants and vowels.
		"""
		'''
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
		'''
		
	def generate(self):
		"""
		generate implements a sample function which generates a word with random
		length. The system makes a distinction between consonants and vowels and generates
		words by using a self.generateVowel variable, which adapts to the feedback.
		"""
		insult = self.get_insult()	
		explanation = ": Thou art " + self.get_insult() + "."
		#explanation = "I find the insultness to be as high as I prefer."
		self.propose(insult, explanation)
		
	def adapt(self, feedback):
		"""
		adapt implements a sample function which changes the self.generateVowel
		according to the feedback of other agents.
		"""
		'''
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
		'''
		
	
	def get_insult(self):
		r = [random.randint(0, len(self.insults[:]) - 1) for t in [0, 0, 0]]
		return self.insults[r[0]][0] + " " + self.insults[r[1]][1] + " " + self.insults[r[2]][2]		
		
	def read_insults(self):
		insults = []
		with open(self.insults_file, "r") as f:
			for line in f.readlines():
				print line
				a, b, c = line.split()
				insults.append([a, b, c])
				self.all_words.append(a)
				self.all_words.append(b)
				self.all_words.append(c)
		return insults
			
			
		
		