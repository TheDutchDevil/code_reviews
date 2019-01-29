'''
Uses the method proposed by Bosu et al. to find effective comments, and tag
them as such. Due to the complexity of this calculation we run this once and
store the results, instead of computing it on the fly. 
'''

from json import JSONEncoder
from time import sleep

import github
import gh_tokens
import datetime
import traceback

from math import ceil
from pymongo import MongoClient

import queue
from analysis.effective_comments.find_effective import process_pr as find_effective

'''
Take a chunk of pull_requests, and find the effective comments in those pull 
requests
'''
def process_pr_chunk(chunk):
    
    print("Starting processing a chunk of size {}".format(len(chunk)))  
    
    mongo_client = MongoClient()
    
    database = mongo_client["graduation"]
    
    commits_collection = database["commits"]

    pull_requests_collection = database["pull_requests"]
    
    for pr in chunk:
        if len(pr["commits"]) == 0:
            continue

        process_pr(pr, commits_collection, pull_requests_collection)

def process_pr(pr, commits_collection, pull_requests_collection):
    
    try:

        full_pr = pull_requests_collection.find_one({'_id': pr["_id"]})

        full_commits = [commits_collection.find_one({'sha': hash}) for hash in full_pr["commits"]]

        hashes = full_pr["commits"]

        full_pr["commits"] = full_commits

        effective_comments = find_effective(full_pr)

        for comment in full_pr["review_comments"]:
            comment["is_effective"] = False

        for effective in effective_comments:
            matching_comment = [comment for comment in full_pr["review_comments"] if comment["url"] == effective[0]["url"]][0]
            matching_comment["is_effective"] = True

        pull_requests_collection.update({'_id':full_pr["_id"]}, {'$set': {'review_comments': full_pr["review_comments"]}})

    except Exception as e:
        print("Failed PR {}/{}:{} with {}\n{}".format(
            pr["project_owner"], pr["project_name"], pr["number"],
            e, traceback.print_tb(e.__traceback__)
        ))

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

projects_list = list(projects_collection.find({'succeeded':True, 'travis_is_oldest_ci': True}))

pr_list = []

for proj in projects_list:
    pr_list.extend(list(pull_requests_collection.find({'project_name': proj["full_name"].split("/")[1],
                                        'project_owner': proj["full_name"].split("/")[0], 'updated_dates': {'$exists': False}},
                                        {'project_owner':1, 'project_name':1, 'commits':1, 'number':1})))

todo_prs = chunkIt(pr_list, 8)

print("Loaded and chunked the commit list")

import multiprocessing
from functools import partial

print("Starting to split of threads \n")    

m = multiprocessing.Manager()

with multiprocessing.Pool(8) as p:
    func = partial(process_pr_chunk)
    p.map(func, todo_prs)
