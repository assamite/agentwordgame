# This is a file which defines the attributes of this agent.
# Please follow the example.
#
# NB! For determining the function name we are parsing the source code. Please
# do not put a spacebar between the function name and parenthesis.
# NNB! In the name (e.g. Phrase length (standard)), the suffix (standard) refers
# to the fact, that these are methods, which come with the original source.
# For your own methods not add anything to the parenthesis (e.g. the example of numberOfWords)

<sampleattribute>
# This attribute is not included and is considered an example. This is included
# as a standard attribute below
<name>
Number of Words
</name>
<function>
def numberOfWords(phrase):
	return len(phrase.split)
	</function>
</sampleattribute>

<attribute>
<name>
Phrase Length (standard)
</name>
	<function>
def phraseLength(phrase):
	return len(phrase)
	</function>
</attribute>

<attribute>
<name>
Phrase Vowels (standard)
</name>
<function>
def phraseVowels(phrase):
	vowels = "aeiou"
	return len(filter(lambda x: x in vowels, phrase))
</function>
</attribute>

<attribute>
<name>
Phrase Consonants (standard)
</name>
<function>
def phraseConsonants(phrase):
	consonants = "bcdfghjklmnpqrstv"
	return len(filter(lambda x: x in consonants, phrase))
	</function>
</attribute>

<attribute>
# This attribute is not included and is considered an example.
<name>
Number of Words (standard)
</name>
<function>
def numberOfWords(phrase):
	return len(phrase.split)
	</function>
</eattribute>