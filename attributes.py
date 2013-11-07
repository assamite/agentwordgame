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