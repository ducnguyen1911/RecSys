__author__ = 'duc07'

import nltk
import string
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer

path = '/home/duc07/data'
token_dict = {}
stemmer = PorterStemmer()


def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))

    return stemmed


def tokenize(text):
    tokens = nltk.word_tokenize(text)
    stems = stem_tokens(tokens, stemmer)
    print "Stemmed: ", stems, "\n"
    return stems

for subdir, dirs, files in os.walk(path):
    for file in files:
        file_path = subdir + os.path.sep + file
        shakes = open(file_path, 'r')
        text = shakes.read()
        lowers = text.lower()
        no_punctuation = lowers.translate(None, string.punctuation)
        token_dict[file] = no_punctuation

#this can take some time
tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
tfs = tfidf.fit_transform(token_dict.values())
print "Token dict: ", token_dict

print "\nResult: ", tfs

str = 'this is a new file'
response = tfidf.transform([str])
print "Response result: ", response

feature_names = tfidf.get_feature_names()
print 'List terms: ', feature_names

from sklearn.metrics.pairwise import cosine_similarity
print "Result: consine similarity = ", cosine_similarity(response, tfs)
