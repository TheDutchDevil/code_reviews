from bs4 import BeautifulSoup
from markdown import markdown
from nltk.tokenize import sent_tokenize
from nltk import ngrams
from nltk.corpus import stopwords
from collections import Counter

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

BOT_NAMES = ["coveralls", 
             "codecov-io",
             "slnode", 
             "pep8speaks", 
             "rh-atomic-bot", 
             "cesium-concierge", 
             "azurecla", 
             "greenkeeperio-bot", 
             "msftclas"]


def given_text_extract_usernames(text):
    if text is None:
        return []

    matches = re.findall(USERNAME_REGEX, text)

    return [match[1] for match in matches]

def is_bot_comment(user_name):
    return user_name in BOT_NAMES

'''
This function removed all quoted text and large code blocks from the input 
parameters, and returns a cleaned string
'''
def clean_text(text):
    # This regex removes the quote characters from the GH issue or comment text.
    cleaned_text = re.sub("^(On[\s\S]*?notifications@github\.com\s*?wrote:\s*?)?(^(\>).*\s)*", '', text, flags=re.MULTILINE)

    # This regex removed all large code blocks
    cleaned_text = re.sub("```[a-z]*\n[\s\S]*?\n```", "", cleaned_text)

    return cleaned_text

'''
Given a text places metatokens for things like, emails, @mentions, usernames,
pieces of code, issue mentions, urls, and version numbers

An optional parameter for this function is a list of names, literal occurences
of these names can then be replaced by the M_USERNAME meta-token.
'''
def tokenize_text(text, names=[]):
    tokenized_text = re.sub("\S+@\S*\s?", ' M_EMAIL ', text, flags=re.MULTILINE)

    tokenized_text = re.sub(USERNAME_REGEX, ' M_MENTION ', tokenized_text, flags=re.MULTILINE)

    tokenized_text =  re.sub("`([\s\S])*?`", " M_ICODE ", tokenized_text)

    tokenized_text = re.sub("(\d)+\.(\d)+(\.(\d)+)*", " M_VERSION_NUMBER ", tokenized_text)

    tokenized_text = re.sub("(\ |^)#\d+", " M_ISSUE_MENTION ", tokenized_text)

    tokenized_text = re.sub("(http|ftp|https|localhost):\/\/([\w_-]+(?:(?:\.[\w_-]+)*))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?", " M_URL ", tokenized_text)

    if len(names) > 0:
        tokenized_text = re.sub("(\s|^)({})(\s|$|[\.\,\!\?\:\;])".format("|".join(re.escape(name) for name in usernames)), ' M_USERNAME ', tokenized_text, flags=re.MULTILINE)

    return tokenized_text

def add_text_ngrams_to_counter(text, html_url, ngram_length, counter, linkback, usernames):
    original_text = text

    if text is None or text == "":
        return

    cleaned_text = clean_text(text)

    tokenized_text = tokenize_text(cleaned_text, names = usernames)
    
    # Removes all markdown content.
    html = markdown(tokenized_text)
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

'''
Given two counters this code returns two new counters, 1 --> 2 and 2 --> 1. 

1 --> 2 Contains all terms that occur in 2 but that don't occur in 1, and 
2 --> 1 Contains all terms that occur in 1 but that don't occur in two. In
addition to containing the terms, the frequence of these terms is also returned.

To prevent the problem that if a very frequent term in 2 occurs only once in 1, 
and therefore won't be part of 1 --> 2 an exclusion threshold can be specified.
This exclusion threshold only considers items with a frequency higher than the 
threshold in the from counter. By default this value is 0.
'''
def compute_deltas(counter_1, counter_2, threshold = 0):
    def compute_delta(counter_from, counter_to, threshold):
        keys_from = [key for key in counter_from.keys() if counter_from[key] > threshold]

        delta = counter_to.keys() - keys_from

        counter_res = Counter()

        for key in delta:
            counter_res[key] = counter_to[key]

        return counter_res

    return (compute_delta(counter_1, counter_2, threshold), 
            compute_delta(counter_2, counter_1, threshold))