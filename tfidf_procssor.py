import io

__author__ = 'ducna3'

import nltk
#nltk.download()
import string
import os
import json
import unicodedata
import sys
import HTMLParser
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer

import elasticsearch
from elasticsearch import helpers

input_folder_path = 'C:\\Users\\ducna3\\1.data\\'
folder_path = 'C:\\Users\\ducna3\\1.data\\data'
token_dict = []
stemmer = PorterStemmer()
# json_file_path = 'C:\\Users\\ducna3\\1.data\\1productItems_1391.json'
json_file_path = '/home/duc07/data/1productItems_1089.json'
cat_id = 1391

flag_es_dict = {}

def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed


def tokenize(text):
    tokens = nltk.word_tokenize(text)
    stems = stem_tokens(tokens, stemmer)
    # print "Stemmed: ", stems, "\n"
    return stems


# calculate similarity scores for each product to all other products
# then sort scores and select top similar products for current product
# select top N similar products
def pprint(i, ls_top_sim):
    print "Result consine similarity for product ", i, "\n"
    # for item in ls_top_sim:
    #     print item[0], ' - ', item[1].encode('utf-8'), ' - ', item[2], '\n',


def save_to_elasticsearch(pItemId, pItemName, ls_top_sim):
    bulk_data = []

    INDEX_NAME = 'recsys_tfidf_result'
    es = elasticsearch.Elasticsearch([{'host': '10.220.83.22', 'port': 9206}])

    # es.indices.delete(INDEX_NAME)
    # es.indices.create(INDEX_NAME)

    ls_rel_p = []
    for rel_prod in ls_top_sim:
        rel_prod_id = rel_prod[0]
        rel_prod_name = rel_prod[1]
        rel_score = rel_prod[2]
        rel_item = {}
        rel_item["similar_score"] = rel_score
        rel_item["similar_product_id"] = rel_prod_id
        rel_item["similar_product_name"] = rel_prod_name
        ls_rel_p.append(rel_item)
    op_dict = {
        '_type': 'tfidf_result_type',
        '_index': INDEX_NAME,
        "_product_id": pItemId,
        "_product_name": pItemName,
        "_ls_similar_products": ls_rel_p,
        # "_rating": row[2]
    }
    bulk_data.append(op_dict)
    print bulk_data
    # bulk index the data
    print("bulk indexing...")
    # res = es.bulk(index=INDEX_NAME, body=bulk_data, refresh=True)
    helpers.bulk(es, bulk_data)


def write_similar_products_of_item_to_file(i, token_dict, ls_top_sim):
    #  # saving into files will take a lot of space
    # with open(folder_path + "\\" + str(cat_id) + "\\" + str(i) + ".txt", "wb") as f:
    #     for item in ls_top_sim:
    #         f.write(item[0].encode('UTF-8') + "," + item[1].encode('UTF-8') + "," + str(item[2]) + "\n")

    # store to ElasticSearch
    pItemId = token_dict[i][0]
    pItemName = token_dict[i][1]
    if pItemId in flag_es_dict:
        print 'Conflict when saving productItemId: ' + str(pItemId) + '\n'
    else:
        flag_es_dict[pItemId] = 1
    save_to_elasticsearch(pItemId, pItemName, ls_top_sim)


# Get top similar ProductItems of item i
def get_top_similar(tfs, i, token_dict):
    # print "test"
    # print "Result consine similarity for product ", i, cosine_similarity(tfs[i], tfs)
    ls_cos = cosine_similarity(tfs[i], tfs)
    ls_cos_id = []
    for j in range(0, ls_cos.size):
        ls_cos_id.append([j, ls_cos[0][j]])  # (id, score)
    sorted_ls_cos_id = sorted(ls_cos_id, key=lambda x: -x[1])
    ls_top_sim = []
    for tuple_score in sorted_ls_cos_id:
        if tuple_score[1] > 0.1:# can filter low scores here ----------------------------------
            ls_top_sim.append(token_dict[tuple_score[0]] + [tuple_score[1]])

    if not os.path.exists(folder_path + "\\" + str(cat_id)):
        os.makedirs(folder_path + "\\" + str(cat_id))
    write_similar_products_of_item_to_file(i, token_dict, ls_top_sim)  # pass token_dict to retrieve pItemId
    return ls_top_sim


# Calculate Matrix of Similarity
def calc_similarity(tfs, token_dict):
    print 'TFS size = ', tfs.shape[0]
    for i in range(0, tfs.shape[0]):  # product_id: ?
        get_top_similar(tfs, i, token_dict)


# Main function for loading json data from file, then processing with tf-idf
def process_tfidf_file(file_path):
    with open(file_path) as data_file:
        productItems = json.load(data_file, encoding='UTF-8')

    tbl = dict.fromkeys(i for i in xrange(sys.maxunicode)
        if unicodedata.category(unichr(i)).startswith('P'))
    h = HTMLParser.HTMLParser()

    for pItem in productItems:
        text = h.unescape(pItem['ProductItemName'])
        lowers = text.lower()
        no_punctuation = lowers.translate(tbl)
        token_dict.append([pItem['ProductItemId'], no_punctuation])
    print "Token dict: ", token_dict

    tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')  # check stop_words: vietnamese?
    tfs = tfidf.fit_transform([x[1] for x in token_dict])  #tfidf.fit_transform(token_dict.values())
    print "\nTf-idf matrix: ", tfs
    feature_names = tfidf.get_feature_names()
    print 'List terms: ', feature_names
    calc_similarity(tfs, token_dict)


def process_tfidf_folder(folder_path):
    from os import path
    files = [f for f in os.listdir(folder_path) if path.isfile(folder_path + f)]
    for f in files:
        # print f
        process_tfidf_file(f)


if __name__ == "__main__":
    process_tfidf_file(json_file_path)
    # process_tfidf_folder(input_folder_path)