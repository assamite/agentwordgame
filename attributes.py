<attribute>
<name>
Phrase Length
</name>
	<function>
def phraseLength(phrase):
	return len(phrase)
	</function>
</attribute>

<attribute>
<name>
Phrase Vowels
</name>
<function>
def phraseVowels(phrase):
	vowels = "aeiou"
	return len(filter(lambda x: x in vowels, phrase))
</function>
</attribute>

<attribute>
<name>
Phrase Consonants
</name>
<function>
def phraseConsonants(phrase):
	consonants = "bcdfghjklmnpqrstv"
	return len(filter(lambda x: x in consonants, phrase))
	</function>
</attribute>