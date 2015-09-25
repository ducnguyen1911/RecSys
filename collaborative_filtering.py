from math import sqrt
from datetime import datetime
import math

books = {}
pitemid_to_prodids = {}
prodid_to_names = {}

# Load dataset and return prefs
def loadDataset(fileName, path=""):
    """ To load the dataSet"
    Parameter: The folder where the data files are stored
    Return: the dictionary with the data
    """
    # Recover the titles of the books

    # for line in open(path + "BX-Books.csv"):
    for line in open(path + "ProductItems.csv"):
        # line = line.replace('"', "")
        # print line, '\n'
        (id, title) = line.split(";")[0:2]
        title = title.replace("\n", "")
        books[id] = title
    for line in open(path + "productitemid_pName_pId.csv"):
        (pitem_id, title, prod_id) = line.split(";")[0:3]
        prod_id = prod_id.replace("\n", "")
        pitemid_to_prodids[pitem_id] = prod_id
        prodid_to_names[prod_id] = title

    # Load the data
    prefs = {}
    count = 0
    # for line in open(path + "BX-Book-Ratings.csv"):
    for line in open(path + fileName):
        line = line.replace('"', "")
        line = line.replace("\\", "")
        # (user, pitemid, rating) = line.split(";")
        (user, pitemid, rating) = line.split(",")
        # try:
        #     if float(rating) > 0.0:
        #         prefs.setdefault(user, {})
        #         # books[pitemid] = 'P-' + str(pitemid)  # ducna added -----------------
        #         if pitemid not in books:
        #             books[pitemid] = 'P-' + str(pitemid)
        #         prefs[user][books[pitemid]] = float(rating)  # using title is not quite true --> bug
        try:
            if float(rating) > 0.0:
                prefs.setdefault(user, {})
                if pitemid not in pitemid_to_prodids:
                    pitemid_to_prodids[pitemid] = 'P-' + str(pitemid)
                if pitemid_to_prodids[pitemid] not in prodid_to_names:  # just added
                    prodid_to_names[pitemid_to_prodids[pitemid]] = pitemid_to_prodids[pitemid]  # just added
                prefs[user][pitemid_to_prodids[pitemid]] = float(rating)

        except ValueError:
            count += 1
            print "value error found! " + user + pitemid + rating
        except KeyError:
            count += 1
            print "key error found! " + user + " " + pitemid
    return prefs


# Returns a distance-base similarity score for person1 and person2
# Disadvantage: only compare in the common set, regardless of difference in size of p1, p2
def sim_distance(prefs, person1, person2):
    # Get the list of shared_items
    si = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            si[item] = 1

    # if they have no rating in common, return 0
    if len(si) == 0:
        return 0

    # Add up the squares of all differences
    sum_of_squares = sum(
        [pow(prefs[person1][item] - prefs[person2][item], 2) for item in prefs[person1] if item in prefs[person2]])

    return 1 / (1 + sum_of_squares)


# Returns the Pearson correlation coefficient for p1 and p2
# Disadvantage: require p1, p2 have same set of features --> need to fill empty ratings.
def sim_pearson(prefs, p1, p2):
    # Get the list of mutually rated items
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1

    # if they are no rating in common, return 0
    if len(si) == 0:
        return 0

    # sum calculations
    n = len(si)

    # sum of all preferences
    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    # Sum of the squares
    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])

    # Sum of the products
    pSum = sum([prefs[p1][it] * prefs[p2][it] for it in si])

    # Calculate r (Pearson score)
    num = pSum - (sum1 * sum2 / n)
    den = sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
    if den == 0:
        return 0

    r = num / den

    return r


# Returns the Cosine similarity for p1 and p2
def sim_cosine(prefs, p1, p2):
    # Get the list of mutually rated items
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1

    # if they are no rating in common, return 0
    if len(si) == 0:
        return 0

    # sum calculations
    n = len(si)

    # sum of all preferences in common set
    sum_r_xy = sum([prefs[p1][it] * prefs[p2][it] for it in si])

    # Sum of the squares of ratings of p1, p2
    sum1Sq = sum([pow(prefs[p1][it], 2) for it in prefs[p1].keys()])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in prefs[p2].keys()])

    # Calculate cosine
    cosine = sum_r_xy / (math.sqrt(sum1Sq) * math.sqrt(sum2Sq))

    return cosine


# Returns the best matches for person from the prefs dictionary #Number of the results
# and similiraty function are optional params.
def topMatches(prefs, person, n=5, similarity=sim_pearson):
    scores = [(similarity(prefs, person, other), other)
              for other in prefs if other != person]
    scores.sort()
    scores.reverse()
    return scores[0:n]


# Gets recommendations for a person by using a weighted average #of every other user's rankings
def getRecommendations(prefs, person, similarity=sim_pearson):
    totals = {}
    simSums = {}

    for other in prefs:
        # don't compare me to myself
        if other == person:
            continue
        sim = similarity(prefs, person, other)

        # ignore scores of zero or lower
        if sim <= 0:
            continue
        for item in prefs[other]:
            # only score books i haven't seen yet
            if item not in prefs[person] or prefs[person][item] == 0:
                # Similarity * score
                totals.setdefault(item, 0)
                totals[item] += prefs[other][item] * sim
                # Sum of similarities
                simSums.setdefault(item, 0)
                simSums[item] += sim

    # Create the normalized list
    rankings = [(total / simSums[item], item) for item, total in totals.items()]

    # Return the sorted list
    rankings.sort()
    rankings.reverse()
    return rankings


# FOR ITEM-BASED RECOMMENDATION ---------------------------------------------------------------
# Function to transform Person, item - > Item, person
def transformPrefs(prefs):
    results = {}
    for person in prefs:
        for item in prefs[person]:
            results.setdefault(item, {})

            # Flip item and person
            results[item][person] = prefs[person][item]
    return results


# Create a dictionary of items showing which other items they are most similar to.
def calculateSimilarItems(prefs, n=10):
    result = {}
    # Invert the preference matrix to be item-centric
    itemPrefs = transformPrefs(prefs)
    c = 0
    for item in itemPrefs:
        # Status updates for large datasets
        c += 1
        if c % 100 == 0:
            print "%d / %d" % (c, len(itemPrefs))
        # Find the most similar items to this one
        scores = topMatches(itemPrefs, item, n=n, similarity=sim_cosine)
        # scores = topMatches(itemPrefs, item, n=n, similarity=sim_distance)
        # scores = topMatches(itemPrefs, item, n=n, similarity=sim_pearson)
        result[item] = scores
    return result


def getRecommendedItems(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}

    # loop over items rated by this user
    for (item, rating) in userRatings.items():

        # Loop over items similar to this one
        for (similarity, item2) in itemMatch[item]:

            # Ignore if this user has already rated this item
            if item2 in userRatings:
                continue
            # Weighted sum of rating times similarity
            scores.setdefault(item2, 0)
            scores[item2] += similarity * rating
            # Sum of all the similarities
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity

    # Divide each total score by total weighting to get an average
    rankings = [(score / totalSim[item_temp], item_temp) for item_temp, score in scores.items()]

    # Return the rankings from highest to lowest
    rankings.sort()
    rankings.reverse()
    return rankings


def store_json(itemMatch):
    import json
    with open('similar_items_09-01-2015.json', 'w') as outfile:
        json.dump(itemMatch, outfile, indent=1, encoding='UTF-8')


def write_similar_products_of_item_to_file(itemMatch):

    # time_str = str(datetime.now().strftime('%Y%m%d-%H%M%S'))
    # with open('output_data\similar_items_08-15-2015_sim_cosine_' + time_str + '.txt', "wb") as f:
    #     for item, ls_similar_items in itemMatch.items():
    #         sum_str = ""
    #         for sitem in ls_similar_items:
    #             # if sitem[0] > 0.5:  # only print recommended items with high similarity
    #                 # sum_str += "[" + str(sitem[0]) + "," + sitem[1].decode('UTF-8') + "]"
    #                 sum_str += "[" + str(sitem[0]) + "," + prodid_to_names[sitem[1]].decode('UTF-8') + "]"
    #         if sum_str != "":
    #             # sum_str = item.decode('UTF-8') + " : [" + sum_str + "]\n"
    #             sum_str = prodid_to_names[item].decode('UTF-8') + " : [" + sum_str + "]\n\n"
    #             f.write(sum_str.encode('utf8'))


    #store cpickle file
    ls_result = {}
    for item, ls_similar_items in itemMatch.items():
        ls_result[item] = []
        pname = prodid_to_names[item]
        ls_result[item].append(pname)
        ls_sim_item_with_name = []
        for sitem in ls_similar_items:
            rel_score = sitem[0]
            rel_pid = sitem[1]
            rel_pname = prodid_to_names[rel_pid].decode('UTF-8')
            ls_sim_item_with_name.append([rel_pid, rel_pname, rel_score])
        ls_result[item].append(ls_sim_item_with_name)

    import cPickle as pickle
    with open("output_data/item_similarity_with_name.cpickle", 'wb') as fp:
        pickle.dump(ls_result, fp)


if __name__ == "__main__":
    print 'start item-based CF ...'
    _prefs = loadDataset("OrderOwner_ProductItem_filter_numbCustperPItem_5_08152015.csv", "input_data/")
    # _prefs = loadDataset("BX-Book-Ratings.csv")
    _itemMatch = calculateSimilarItems(_prefs)
    # store_json(_itemMatch)
    write_similar_products_of_item_to_file(_itemMatch)
    _user_id = '11233'  # set user id
    _rankings = getRecommendedItems(_prefs, _itemMatch, _user_id)
    print "Recommended Items: ", _rankings
