from bs4 import BeautifulSoup
from markdown import markdown
from nltk.tokenize import sent_tokenize
from nltk import ngrams
from nltk.corpus import stopwords

import re
import string
import nltk

contractor = [
    ('pull', 'request'),
    ('commit', 'message'),
    ('os', 'x'),
    ('unit', 'test'),
    ('continuous', 'integration')
]

expandor = [
    ('lgtm', ['looks', 'good', 'to', 'me']),
    ('pr', ['pullrequest']),
    ('ci', ['continuousintegration'])
]

meta_tokens = ["M_EMAIL",
               "M_MENTION",
               "M_ICODE",
               "M_HASH",
               "M_VERSION_NUMBER",
               "M_ISSUE_MENTION",
               "M_URL",
               "M_USERNAME"]

USERNAME_REGEX = "(\ |^)@(\S*\s?)"


def given_text_extract_usernames(text):
    if text is None:
        return []

    matches = re.findall(USERNAME_REGEX, text)

    return [match[1] for match in matches]


def add_text_ngrams_to_counter(text, html_url, ngram_length, counter, linkback, usernames):
    original_text = text

    if text is None or text == "":
        return

    # This regex removes the quote characters from the GH issue or comment text.
    mt_text = re.sub("^(On[\s\S]*?notifications@github\.com\s*?wrote:\s*?)?(^(\>).*\s)*", '', text, flags=re.MULTILINE)

    # Removes all large code blocks
    mt_text = re.sub("```[a-z]*\n[\s\S]*?\n```", "", mt_text)

    # Replace email with meta token
    mt_text = re.sub("\S+@\S*\s?", ' M_EMAIL ', mt_text, flags=re.MULTILINE)

    # Replace mention with meta token
    mt_text = re.sub(USERNAME_REGEX, ' M_MENTION ', mt_text, flags=re.MULTILINE)

    #print(mt_text)

    mt_text = re.sub("(\s|^)({})(\s|$|[\.\,\!\?\:\;])".format("|".join(re.escape(name) for name in usernames)), ' M_USERNAME ', mt_text, flags=re.MULTILINE)

    # This removes inline code snippets and replaces them with a meta token
    mt_text = re.sub("`([\s\S])*?`", " M_ICODE ", mt_text)

    #tokenizes version numbers
    mt_text = re.sub("(\d)+\.(\d)+(\.(\d)+)*", " M_VERSION_NUMBER ", mt_text)

    mt_text = re.sub("(\ |^)#\d+", " M_ISSUE_MENTION ", mt_text)

    mt_text = re.sub("(http|ftp|https|localhost):\/\/([\w_-]+(?:(?:\.[\w_-]+)*))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?", " M_URL ", mt_text)

    # Removes all markdown content.
    html = markdown(mt_text)
    stripped_text = ''.join(BeautifulSoup(html, "lxml").findAll(text=True))

    sentences = sent_tokenize(stripped_text)

    punct_regex = re.compile("^[%s\s]*$" % re.escape(string.punctuation), flags=re.MULTILINE)

    for raw_sentence in sentences:

        sentencetokens_sw = nltk.word_tokenize(raw_sentence)

        looper = 0
        for token in sentencetokens_sw:
            if token not in meta_tokens:
                sentencetokens_sw[looper] = token.lower()

                if sentencetokens_sw[looper] == 'n\'t':
                    sentencetokens_sw[looper] = 'not'

                if sentencetokens_sw[looper] == '\'s':
                    sentencetokens_sw[looper] = 'us'

                if sentencetokens_sw[looper] == '\'m':
                    sentencetokens_sw[looper] = "am"

                if sentencetokens_sw[looper] == '\'d':
                    sentencetokens_sw[looper] = "would"

                if sentencetokens_sw[looper] == '\'re':
                    sentencetokens_sw[looper] = 'are'

                sentencetokens_sw[looper] = punct_regex.sub("", sentencetokens_sw[looper])

            # GitHub commits hashes have a lenth of 40 chars, coveralls seems to use this.
            if len(token) == 40:
                sentencetokens_sw[looper] = " M_HASH "

            looper += 1

        # Adding the following snippets removes stop words: (not token in stopwords.words('english'))
        sentencetokens_sw = [token for token in sentencetokens_sw if
                             ((not token in stopwords.words('english')) and (not token in string.punctuation))]

        merged_sentence_tokens = []

        i = 0

        while i < (len(sentencetokens_sw) - 1):
            merged_pair = False

            for mergepair in contractor:
                if sentencetokens_sw[i] == mergepair[0] \
                        and sentencetokens_sw[i + 1] == mergepair[1]:
                    merged_sentence_tokens.append(mergepair[0] + mergepair[1])
                    i += 2
                    merged_pair = True
                    break

            if not merged_pair:
                merged_sentence_tokens.append(sentencetokens_sw[i])
                i += 1

        expanded_sentence_tokens = []

        i = 0

        while i < len(merged_sentence_tokens) - 1:

            expanded = False
            for expand in expandor:
                if merged_sentence_tokens[i] == expand[0]:
                    expanded = True
                    for item in expand[1]:
                        expanded_sentence_tokens.append(item)

            if not expanded:
                expanded_sentence_tokens.append(merged_sentence_tokens[i])

            i += 1

        porter = nltk.PorterStemmer()
        looper = 0
        for token in expanded_sentence_tokens:
            if token not in meta_tokens:
                expanded_sentence_tokens[looper] = porter.stem(token)
            looper += 1

        for ngram in ngrams(expanded_sentence_tokens, ngram_length):
            
            
            if ngram not in linkback:
                linkback[ngram] = []                
            
            linkback[ngram].append({"sentence": raw_sentence, "text": original_text, "url": html_url})
            counter[ngram] += 1
