import agent
import random
import time

class AgentImpl(agent.Agent):

	def __init__(self, name):
		# Anything you want to initialize
		self.vowelWeight = random.random()
		self.consonantWeight = random.random()
		self.generateVowel = 0.5
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
		total = vowels + consonants
		scr = 1 - abs(self.vowelWeight - (vowels/total)) - abs(self.consonantWeight - (consonants/total))
		return scr
		
	def generate(self):
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
		explanation = ""
		## If the word is ready, propose it to the server
		self.propose(word, explanation)
		
	def adapt(self, feedback):
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