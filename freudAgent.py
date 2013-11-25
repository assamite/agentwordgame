import os
import re
import json
import random
import time
import operator
import urllib2
import logging
import traceback
from timeit import default_timer as timer
from urlparse import urljoin

from google import search

from bs4 import BeautifulSoup as bs
from bs4 import CData
import nltk
from nltk.corpus import stopwords

import Levenshtein as lv


import agent
from agent import Feedback

class FreudAgent(agent.Agent):
    """ Siegmund Freud agent which slips "inappropriate" phrases depending
        on the given word_file. Agent replaces words from given phrases to
        words it finds from the word_file and rates words depending if they are
        found from the file or not.
        
        params:
        word_file    : File containing a tag and list of words, separated by
        white spaces on each line. Tag should start with one of the following: 
        'n', 'a' 'v' and 'r', which correspond to noun, adjective, verb and 
        adverb, respectively. 
        context     :  Give a meaningful context string for the words found in 
        the word_file. This context is googled for finding more words. To add 
        to the replaceable word's list.

        Adapted from: http://github.com/assamite/Slipper 
    """
    def __init__(self, name, word_file = os.path.join(os.path.dirname(__file__), "sexuality.txt"), context = 'sexuality'):
        # Anything you want to initialize
        #self.name = "Siegmund Freud"
        self.name = name
        self.vowelWeight = random.random()
        self.consonantWeight = random.random()
        self.generateVowel = 0.5

        # Dictionary, key: context-string value: POS-dictionary 
        # POS-dictionary contains key for each POS-tag (treebank tags) and 
        # values are words for that tag in this context.
        self.POSs = {context: self.read_wordnet(word_file) }
        # Dictionary, key: context-string, value: how many google search have
        # been done  to get urls for this context.
        self.context_google_amounts = {context: 0}
        # Dictionary, key: context-string, value: current weight of the context,
        # should be adapted based on the feedback. New phrases are added from 
        # the context with highest weight to current proposes.
        self.context_weights = {context: 1.0}
        # Current proposes for new phrases.
        self.current_proposes = []     
        # Phrase - context dictionary for remembering former phrases agent has
        # published.
        self.own_phrases = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler())
        
        # Noun phrase extraction tools for arbitrary text.
        self.lemmatizer = nltk.WordNetLemmatizer()
        self.stemmer = nltk.stem.porter.PorterStemmer()
        self.stopwords = stopwords.words('english')
        self.chunker = nltk.RegexpParser(self.grammar)
        
        agent.Agent.__init__(self, self.name)
    
        
    def lifeCycle(self):
        """
        The function which is repeatedly started and defines the behaviour
        of the agent in the context of adaption, scoring and generating.
        """
        r = random.random()

        if r < 0.33:
            self.generate()
        if r > 0.33 and r < 0.66:
            ## Gives the lists of lists, where each sublist is, ordered by timestamp desc:
            ## [Word, Word], see documentation
            unratedwords = self.getUnscoredWords()
            w = unratedwords[0]
            w 
            
            scr = self.score(w.word)
            framing = "This is not a nice word"
            self.sendFeedback(w.word_id, scr, framing, wordtext=w.word)
        elif r > 0.66:
            ## The result is the following:
            ## [Feedback, Feedback], see documentation
            feedback = self.getAllFeedback()
            self.adapt(feedback)
            
        time.sleep(0.5)
        
        
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
        """ Take first from current_proposes or makes a new google search for 
        new proposes with the current highest weighing context.

        """
        if len(self.current_proposes) > 0:         
            print("Getting sentences from old result.")
            proposition = self.current_proposes.pop()
            explanation = "I find the attribute inappropriateness in context of %s to be as high as I prefer" % (proposition[1])
            self.propose(proposition[0].encode(encoding = 'ascii', errors = 'replace'), explanation)
            
        else:  
            # Do a Google search for the most weighted context and get the first
            # result which is not parsed yet in the agent's life cycle.
            context = self.get_context()
            googles = self.context_google_amounts[context]
            weight = self.context_weights[context]
            print("Search %d for %s with weight %f" % (googles, context, weight))
            
            # Get next results until some freudified phrases are found.
            found = False
            while not found:
                self.context_google_amounts[context] += 1
                # Returns a generator which yields google search results.
                results = search(context, num = 1, start = googles, stop = googles + 1, pause = 2.0)
                googles = self.context_google_amounts[context]
                
                # TODO: How does the generator exit if there are no more results?
                try:
                    url = results.next() 
                    print url
                except:
                    break    
                
                # Freudify the source.
                source = self.get_source(url)
                if source is None:
                    continue
                phrases = self.freudify_source(source, url)
                if len(phrases) > 0:
                    found = True
                    print("Found %d sentences from %s" % (len(phrases), url))
                    self.current_proposes = phrases[1:]
                    explanation = "I find the attribute inappropriateness in context of %s to be as high as I prefer" % (phrases[0][1])
                    self.propose(phrases[0][0].encode(encoding = 'ascii', errors = 'replace'), explanation)
                    break
                
            # No more results for this context I suppose. 
            if found is False:
                self.context_weights[context] = -1 
            
            
            
            #result = gs.get_results()[googles % (gs.page * 50)]
            #print result.url
            
            
            #explanation = "I find the attribute inappropriateness to be as high as I prefer"
            #self.propose(word, explanation)
    
        
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
        

    ####################################################
    # Utility functions for Freud agent. 
    
    # Adapted from: https://github.com/assamite/Slipper
    ####################################################
    
    def get_context(self):
        ''' Get currently highest weighing context. '''
        return 'sexuality'
        
        
    def get_source(self, url):
        '''
            Gets source code from 'url' and returns it. If error happens while 
            getting the source returns None and if page returns HTTP code >= 400
            returns the code as int.
        '''
        self.logger.info("Getting source from: %s" % url)
        try:
            response = urllib2.urlopen(url)
            self.logger.info("Got %s response from %s" % (response.getcode(), url))
        except:
            self.logger.error("Could not get source from: %s" % url)
            self.logger.error("Error stack \n %s" % traceback.format_exc())
            return None
        if response.getcode() and response.getcode() > 399: 
            return response.getcode()
        page_source = response.read()
        if len(page_source) > 10000000: # Magic number
            return -1
        return page_source
    
    
    def read_wordnet(self, filepath):
        '''
            Reads 'sexuality.txt' and returns it as a dictionary with part of speech
            tags as keys and words as values. 
        '''
        f = open(filepath)
        s_words = {}
        repl_tags = {'n':'NN','a':'JJ','v':'VB','r':'RB'}
    
        for l in f.readlines():
            t = l.split()
            tag = repl_tags[t[0][0]]
            ws = t[1:]
            for w in ws:
                w = w.replace('_', ' ')
                try:
                    s_words[tag].append(w)
                except KeyError:
                    s_words[tag] = [w]
                    
        s_words['NNP'] = s_words['NN']
        return s_words
    
    
    def replace_document_words(self, words, tagged_words):
        '''
            Iterates over all the words in the document and finds suitable replacing 
            words for nouns, adjectives and adverbs from POSs POS-dictionary.
        
            Parameters
            words:            iterable of tokenized raw words.
            tagged_words:    iterable of (raw word, tag) pairs
        
            Returns altered iterable where some of the words may have been replaced
            with the words from POSs.
        '''
        altered_words = []
        
        # magic numbers for max levenshtein distance. key: len(word), value: max lv
        maxlv = {3: 1, 4: 1, 5: 2, 6: 2, 7:2, 8: 3, 9: 3, 10: 3, 11: 3}
        alter_amount = 0
    
        for i, w in enumerate(words):
            altered_words.append(w)
            if len(w) < 3: continue
            tag = tagged_words[i][1][:2]
            if tag in self.POSs['sexuality'].keys():
                lv = 1
                if len(w) in maxlv.keys(): lv = maxlv[len(w)]
                else: lv = 4
                rp = self.replace_word(lv, tag, w)[0]    
                if not rp.lower() == w.lower():
                    if w[0].isupper(): rp = rp.title()
                    altered_words[i] = rp    
                    alter_amount += 1
        return altered_words, alter_amount
    
    
    def replace_word(self, tag, word):
        '''
            Checks if there is suitable replace word from all POSs for 'word'.
        
            Parameters:
            tag:    word's position tag (noun, verb, etc)
            word:    word to find replace for
            
            Returns (word, levenshtein distance, context) of the best
            replaceable word found from POSs, if no replacing word is found,
            returns (input word, 0, '').
        '''
        # magic numbers for max levenshtein distance. key: len(word), value: max lv
        levenshteins = {3: 1, 4: 1, 5: 2, 6: 2, 7:2, 8: 3, 9: 3, 10: 3, 11: 3}
        maxlv = 1 
        if len(word) in levenshteins.keys(): maxlv = levenshteins[len(word)]
        else: maxlv = 4
        
        word = word.lower()
        dists = []
        for context, POS in self.POSs.items():
            if tag in POS:
                for w in POS[tag]:
                    dists.append((w, lv.distance(word, w), context))
                dists = sorted(dists, key=operator.itemgetter(1))
            if len(dists) > 0 and dists[0][1] <= maxlv: # Let's take first one always. It's good
                return dists[0]      # to be coherent with these, so that some 
            else:                            # sense is maintained in the text.
                return (word, 0, '')
        
    
    # TODO: FIX ME
    def prettify_sentence(self, replaced_words):
        '''
            Prettify given iterable that represents words and part of words and 
            other characters of the sentence. ie, there can be indeces with only
            "'ll" or "'" in them.
            
            Kinda hackish code, which could be looked into at some point of time.
            
            Parameters:
            replaced_words:    Iterable with sentence's words and other characters. 
                            This iterable is considered to be created by nltk >=2.04
                            part of speech tagging (and replacing some words in it).
            
            Returns prettified sentence as one string.
        '''
        pretty_sentence = ""
        last_word = ""
        enc_hyphen = False
        
        for w in replaced_words:
            if w in ["``", "\""]:
                pretty_sentence += " \""
            elif w == "''":
                pretty_sentence += "\""
            elif w in [',', '!', '?', '.', '%', '\"', "n't", "'re", "'s", ";", ":", ")", "]", "}", "'m", "'ll", "'s", "'d"]:
                pretty_sentence += w
            elif w in ['\'']: 
                if enc_hyphen:
                    pretty_sentence += w
                    enc_hyphen = False    
            elif last_word in ["``", "(", "[", "{", "\""]:
                pretty_sentence += w    
            else:
                pretty_sentence += " " + w
            if w.startswith("'") and w not in ["'m", "'d", "'re", "'s", "'ll"]: 
                enc_hyphen = True
            last_word = w
            
        pretty_sentence.strip()  
        return pretty_sentence
        
        
    # FIXME: probably not everything is correct in here.    
    def visible_html_tag(self, element):
        '''
            Checks if given element in soup parsed by BeautifulSoup is visible to 
            the site's viewer or not.
            
            Parameters:
            element:    element to be checked
            
            Returns True if element is visible, otherwise returns False.
        '''
        if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
            return False
        if element.name in ['script', 'style', '[document]']: 
            return False
            ''' 
            if element.name and 'style' in element.attrs:
                #print element['style']
                if re.match(r'display:(\s*)none', element['style']):
                    return False
            if element.parent.name and 'style' in element.parent.attrs:
                print element.parent['style']
                if re.match(r'display:(\s*)none', element.parent['style']):
                    return False
            '''
        elif re.match(u'.*<!--.*-->.*', str(element), re.DOTALL):
            return False
        return True
        
        
    def freudify_source(self, source, url):
        '''
            Freudifies given source's noun phrases and returns them as 
            list.
            
            Basically calls BeautifulSoup to soup the source and then calls 
            extract_noun_phrases and replace_words for all the phrases.
            
            Parameters:
            source:     source code of the site
            url:        url of the site
            
            Returns changed source code.
        '''
        s = timer()
        soup = bs(source, 'lxml')
        self.logger.info("Souped %s in %s" % (url, str(timer() - s)))
        phrases = []
        
        try:
            t = timer()
            phrases = self.extract_noun_phrases(soup)
            self.logger.info("Freudified %s in %s" % (url, str(timer() - t)))
        except:
            self.logger.info("utils.slip_sentences has blown, with stack trace: \n %s" % traceback.format_exc())
            return []
            
        self.logger.info("Finished tagging source from: %s " % url)
        return phrases
    
    
    def extract_noun_phrases(self, soup):
        ''' Extract noun phrases from given soup and slip them. '''
        
        noun_phrases = []
        
        for t in soup.body.descendants:
            if not hasattr(t, 'name'): continue
    
            if self.visible_html_tag(t) and hasattr(t, 'string'):
                if t.string == None: continue
                if isinstance(t, CData): 
                    continue
                
                phrases = self.extract(t.string)
                
                if phrases is not None and len(phrases) > 0:
                    noun_phrases.extend(phrases)
                    
        return noun_phrases
    
    
    ################################################################
    # Following functionality is mostly ripped (and altered) from 
    # https://gist.github.com/alexbowe/879414
    #
    # Hence some self variables are defined here for integrity.
    ################################################################
    
         
    #Taken from Su Nam Kim Paper...
    grammar = r"""
        VBAR: 
            {<V.*><NN.*|JJ>*<NN.*>}
    
        NBAR:
            {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
            
        NP:
            {<NBAR>}
            {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
            {<VBAR>}
            {<VBAR><IN><NBAR>}
    """
    
            # Used when tokenizing words
    sentence_re = r'''(?x)      # set flag to allow verbose regexps
          ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
        | \w+(-\w+)*            # words with optional internal hyphens
        | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
        | \.\.\.                # ellipsis
        | [][.,;"'?():-_`]      # these are separate tokens
    '''
    
    chunker = nltk.RegexpParser(grammar)
    
    def extract(self, text):
        ''' Extract and freudify noun phrases from text, return all succesfully
        freudified noun phrases. '''
        
        toks = nltk.regexp_tokenize(text, self.sentence_re)
        postoks = nltk.tag.pos_tag(toks)
        tree = self.chunker.parse(postoks)
        terms = self._get_terms(tree)
        
        phrases = []
        
        # Loop through all the noun phrases and try to freudify them.
        for term in terms:
            changed = False
            context = ""
            phrase = []
            for part in term:
                word, tag = part
                phrase.append(word)
                rpl = self.replace_word(tag[:2], word)
                if len(rpl[2]) > 0:
                    context = rpl[2]
                    phrase[-1] = rpl[0]
                    changed = True
            if changed:
                phrase = " ".join(phrase).strip()
                phrases.append((phrase, context))    
                
        return phrases
          
    def _leaves(self, tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.node=='NP'):
            yield subtree.leaves()
     
    def _normalise(self, word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        word = self.stemmer.stem_word(word)
        word = self.lemmatizer.lemmatize(word)
        return word
     
    def _acceptable_word(self, word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
            and word.lower() not in self.stopwords)
        return accepted
         
    def _get_terms(self, tree):
        terms = []
        for leaf in self._leaves(tree):
            terms.append([(w, t) for w,t in leaf if self._acceptable_word(w)])
        return terms
         
        
test = "The buttocks (singular: buttock) are two rounded portions of the anatomy, located on the posterior of the pelvic region of apes and humans, and many other bipeds or quadrupeds, and comprise a layer of fat superimposed on the gluteus maximus and gluteus medius muscles. Physiologically, the buttocks enable weight to be taken off the feet while sitting. In many cultures, they play a role in sexual attraction. Many cultures have also used them as a safe target for corporal punishment. There are several connotations of buttocks in art, fashion, culture and humor, and the English language is replete with many popular synonyms. In humans they are located between the lower back and the perineum."      
        
        