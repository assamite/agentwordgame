import os
import re
import json
import sets
import random
import time
import operator
import urllib2
import logging
import traceback
import timeit
import urlparse
import pickle

import google

import bs4
import nltk

import Levenshtein


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

        # Dictionary, key: context-string value: POS-dictionary 
        # POS-dictionary contains key for each POS-tag (treebank tags) and 
        # values are words for that tag in this context as a set.
        self.POSs = {context: self.read_wordnet(word_file) }
        self.accepted_pos = ['NN', 'NNP', 'JJ', 'RB', 'VB']
        # Dictionary, key: context-string, value: how many google search have
        # been done  to get urls for this context.
        self.context_google_amounts = {context: 0}
        # Dictionary, key: context-string, value: current weight of the context,
        # should be adapted based on the feedback. New phrases are added from 
        # the context with highest weight to current proposes.
        self.context_weights = {context: 1.0}
        # Current proposes for new phrases.
        self.current_proposes = []     
        # context of current_proposes
        self.current_context = ""
        # Phrase - context dictionary for remembering former phrases agent has
        # published.
        self.own_phrases = {context: sets.Set()}
        
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.DEBUG)
        
        # Noun phrase extraction tools for arbitrary text.
        self.lemmatizer = nltk.WordNetLemmatizer()
        self.stemmer = nltk.stem.porter.PorterStemmer()
        self.stopwords = nltk.corpus.stopwords.words('english')
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
            #pass
        if r > 0.33 and r < 0.66:
            ## Gives the lists of lists, where each sublist is, ordered by timestamp desc:
            ## [Word, Word], see documentation
            unratedwords = self.getUnscoredWords()
            if len(unratedwords) > 0:
                w = unratedwords[0]
                score = self.score(w.word)
                framing = "I like the sex...*ermm* score of this pen..*ahem* word to be very boo...unrelated to anything."
                self.sendFeedback(w.word_id, score, framing, wordtext=w.word)
        elif r > 0.66:
            ## The result is the following:
            ## [Feedback, Feedback], see documentation
            feedback = self.getAllFeedback()
            self.adapt(feedback)
            #pass
            
        time.sleep(0.2)
        
        
    def score(self, word):
        """
        If phrases words are found from context dictionary, score will be goood.
        returns | found words | / phrase length.
        """
        words = word.split()
        context_words = 0.0
        
        for w in words:
            found = False
            for context, poss in self.POSs.items():
                for pos, word_list in poss.items():
                    for word in word_list:
                        if word == w:
                            found = True
            if found:
                context_words += 1
        
        return context_words / len(words)
        
        
    def generate(self):
        """ Take first from current_proposes or makes a new google search for 
        new proposes with the current highest weighing context.

        """
        if len(self.current_proposes) > 0:
            print("Trying to get a phrase from old result.")
            while len(self.current_proposes) > 0:     
                proposition = self.current_proposes.pop()
                if proposition[0] not in self.own_phrases[proposition[1]]:
                    explanation = "I find the inappropriateness in context of %s to be ass butt.. *krhm* high as I prefer" % proposition[1]
                    self.own_phrases[proposition[1]].add(proposition[0])
                    self.propose(proposition[0].encode(encoding = 'ascii', errors = 'replace'), explanation)
                    return
              
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
            results = google.search(context, num = 1, start = googles, stop = googles + 1, pause = 2.0)
            googles = self.context_google_amounts[context]
            
            # TODO: How does the generator exit if there are no more results?
            try:
                url = results.next() 
            except:
                print traceback.format_exc()
                break    
            
            # Freudify the source.
            source = self.get_source(url)
            if source is None:
                print "Could not retrieve source from %s" % url
                continue
            phrases = self.freudify_source(source, url)
            if len(phrases) > 0:
                found = True
                print("Found %d sentences from %s" % (len(phrases), url))
                self.current_context = context
                if len(phrases) >= 20:
                    self.current_proposes = phrases[1:20]
                else:
                    self.current_prposes = phrases[1:len(phrases)]
                explanation = "I find the inappropriateness in context of %s to be ass butt.. *krhm* high as I prefer" % context
                self.propose(phrases[0][0].encode(encoding = 'ascii', errors = 'replace'), explanation)
                break
            
        # No more results for this context I suppose. 
        if found is False:
            self.context_weights[context] = -1 
    
        
    def adapt(self, feedback):
        """
        Adapt to other agents by doing two things:
            if framing context is observed first time, add words from it to
            context dictionary
            
            adjust context weight of the attribute depending on if it has been
            rated too high or low.
        """
        
        for c in self.context_weights.keys():
            if self.context_weights[c] != -1:
                self.context_weights[c] = 1

        for f in feedback:
            attributes = self.getFramingAttributes(f)
            for a in attributes:
                # If readable name of the attribute is not in the contexts, add it
                if a[0] not in self.POSs.keys():
                    print "Adding %s to context dictionary and doing a google search for words. This might take a while" % a[0]
                    self.POSs[a[0]] = {}
                    self.context_google_amounts[a[0]] = 0
                    self.context_weights[a[0]] = 1
                    self.own_phrases[a[0]] = sets.Set()
                    self.get_new_words(a[0])
                
                # Adjust context weights depending on general opinion
                if self.context_weights[a[0]] != -1: 
                    if a[1] == 'high':
                        self.context_weights[a[0]] *= 0.99 
                        print "Adjusting %s weight, now %f" % (a[0], self.context_weights[a[0]])
                        
                    if a[1] == 'low':
                        self.context_weights[a[0]] *= 1.01 
                        print "Adjusting %s weight, now %f" % (a[0], self.context_weights[a[0]])
                
    
    def get_context(self):
        ''' Get currently highest weighing context. '''
        highest = -100000
        context = self.context_weights.keys()[0]
        for c, i in self.context_weights.items():
            if i > highest:
                highest = i
                context = c
        
        self.context_weights[context] *= 0.95
        return context
    
    def get_new_words(self, context):
        '''
            Do google search with given context and add most observed words to 
            context's word lists in self.POSs with appropriate tags.
        '''
        googles = self.context_google_amounts[context]
        results = google.search(context, num = 15, start = googles, stop = googles + 15, pause = 0)
        self.context_google_amounts[context] = googles + 15
        words = {}
        
        for i in range(2):
            try:
                url = results.next()
                source = self.get_source(url)
                if source is not None:
                    ret = self.get_word_amounts(source, url)
                    for w in ret.keys():
                        amount = ret[w]
                        if w in words.keys():
                            words[w] += amount
                        else:
                            words[w] = amount
            except:
                print traceback.format_exc()
                
        word_list = [(w, words[w]) for w in words.keys()]
        word_list = sorted(word_list, key=operator.itemgetter(1))
        word_list.reverse()
        new_words = 100 if len(word_list) > 100 else len(word_list)
        if context not in self.POSs: self.POSs[context] = {}
        for i in range(new_words):
            w = word_list[i][0]
            if len(w[0]) > 3:
                if w[1] not in self.POSs[context]: self.POSs[context][w[1]] = sets.Set()
                self.POSs[context][w[1]].add(w[0].lower())
        
        amount = 0
        for pos in self.POSs[context].keys():
            amount += len(self.POSs[context][pos])   
        print "Added %d words to %s" % (amount, context)

             

    ####################################################
    # Utility functions for Freud agent. 
    
    # Adapted from: https://github.com/assamite/Slipper
    ####################################################      
        
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
            return None
        page_source = response.read()
        if len(page_source) > 10000000: # Magic number
            return None
        return page_source
    
    
    def read_wordnet(self, filepath):
        '''
            Reads file in given filepath and returns it as a dictionary with 
            part of speech tags as keys and words as values. File in question
            should conform to format where each line starts with a string 
            starting with n (noun), a (adjective), v (verb), r (adverb) followed 
            with a white space and list of words, ie.
            n#155532 cat dog human
            v#43463 run speak walk
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
                w = w.encode('ascii', 'replace')
                try:
                    s_words[tag].add(w)
                except KeyError:
                    s_words[tag] = sets.Set(w)
                    
        s_words['NNP'] = s_words['NN']
        return s_words
    
    
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
                    dists.append((w, Levenshtein.distance(word, w), context))
                dists = sorted(dists, key=operator.itemgetter(1))
            if len(dists) > 0 and dists[0][1] <= maxlv: # Let's take first one always. It's good
                return dists[0]      # to be coherent with these, so that some 
            else:                            # sense is maintained in the text.
                return (word, 0, '')
        
        
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
        elif re.match(u'.*<!--.*-->.*', element.encode('utf8'), re.DOTALL):
            return False
        return True
        
    def get_word_amounts(self, source, url):
        s = timeit.default_timer()
        soup = bs4.BeautifulSoup(source, 'lxml')
        self.logger.info("Souped %s in %s" % (url, str(timeit.default_timer() - s)))
        words = {}
        
        try:
            t = timeit.default_timer()
            for t in soup.body.descendants:
                if not hasattr(t, 'name'): continue
        
                if self.visible_html_tag(t) and hasattr(t, 'string'):
                    if t.string == None: continue
                    if isinstance(t, bs4.CData): 
                        continue
                    
                    sentences = t.string.encode('ascii', 'replace')
                    sentences = nltk.sent_tokenize(sentences)
                    for s in sentences:
                        sent = nltk.word_tokenize(s)
                        tagged = nltk.tag.pos_tag(sent)
                        if len(tagged) > 2:
                            for w in tagged:
                                if w[0] not in self.stopwords and w[1] in self.accepted_pos:       
                                    if w in words.keys():
                                        words[w] += 1
                                    else: 
                                        words[w] = 1
                                #print w, words[w]
                    
            #self.logger.info("Got word amounts %s in %s" % (url, str(timeit.default_timer() - t)))
        except:
            self.logger.info("get_word_amounts has blown, with stack trace: \n %s" % traceback.format_exc())
            return []
            
        self.logger.info("Got %d words from: %s " % (len(words.keys()), url))
        return words
        
        
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
        s = timeit.default_timer()
        soup = bs4.BeautifulSoup(source, 'lxml')
        self.logger.info("Souped %s in %s" % (url, str(timeit.default_timer() - s)))
        phrases = []
        
        try:
            t = timeit.default_timer()
            phrases = self.extract_noun_phrases(soup)
            self.logger.info("Freudified %s in %s" % (url, str(timeit.default_timer() - t)))
        except:
            self.logger.info("freudify_source has blown, with stack trace: \n %s" % traceback.format_exc())
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
                if len(t.string) == 0: continue
                if isinstance(t, bs4.CData): 
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
        
        phrases = sets.Set()
        
        # Loop through all the noun phrases and try to freudify them.
        for term in terms:
            if (len(term)) < 2: continue
            changed = False
            context = ""
            phrase = []
            for part in term:
                word, tag = part
                word = word.encode('ascii', 'replace')
                phrase.append(word.lower())
                rpl = self.replace_word(tag[:2], word)
                if len(rpl[2]) > 0:
                    context = rpl[2]
                    phrase[-1] = rpl[0]
                    changed = True
            if changed:
                phrase = " ".join(phrase).strip()
                phrase.encode('ascii', 'replace')
                phrase = str(phrase)
                if phrase not in self.own_phrases[context]:
                    phrases.add((str(phrase), context))    
          
        phrases = list(phrases)      
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
        
        