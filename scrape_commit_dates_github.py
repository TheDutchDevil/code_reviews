# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 11:21:02 2018

Uses the GitHub API to find the date of commits that cannot be dated through
the instance of GitHub

@author: natha
"""

from json import JSONEncoder
from time import sleep

import github
import gh_tokens
import datetime

from github import Github
from math import ceil
from pymongo import MongoClient

import queue

class IterableQueue():
    def __init__(self,source_queue):
            self.source_queue = source_queue
    def __iter__(self):
        while True:
            try:
               yield self.source_queue.get_nowait()
            except queue.Empty:
               return

class GitHubEncoder(JSONEncoder):
    
    def default(self, o):
        if o is github.GithubObject.NotSet:
            return None
        elif isinstance(o, github.Requester.Requester):
            return o.__dict__
        elif isinstance(o, HTTPSRequestsConnectionClass):
            return None
                
        return json.JSONEncoder.default(self, o)
                

def getRateLimit(g):
    return g.get_rate_limit().core

def getRateLimitSearch(g):
    return g.get_rate_limit().search


def computeSleepDuration(g):
    reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds()))

def computeSleepDurationForRate(rate):
    reset_time = rate.reset
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds()))


def waitIfDepleted(g):    
    rate_limit = getRateLimit(g)
    
    sleep_duration = computeSleepDuration(g)
    if not rate_limit.remaining > 49:
        print("Waiting {} minutes".format(sleep_duration/60))
        sleep(sleep_duration)
    

def waitAndGetRepo(g, slug):
    waitIfDepleted(g)
    return g.get_repo(slug)

def check_header_and_refresh(g, token_queue, depth = 0):
    rate_limits = g.get_rate_limit()
    remaining_core = rate_limits.core.remaining
    remaining_search = rate_limits.search.remaining

    if remaining_core < 50:
        if token_queue.qsize() == 1:
            print("Only one token so waiting")
            waitIfDepleted(g)
        else:        
            new_token = token_queue.get()
            token_queue.put(new_token)
            g._Github__requester._Requester__authorizationHeader = "token " + new_token
            
            rate_limits = g.get_rate_limit()
            remaining_core = rate_limits.core.remaining
            remaining_search = rate_limits.search.remaining
            
            if remaining_core < 50:
                if depth < 3:
                    check_header_and_refresh(g, token_queue, depth=depth+1)
                else:
                    print("New token is depleted, so waiting")
                    waitIfDepleted(g)
                    print("Done waiting")
            elif remaining_search < 2:
                sleep_time = computeSleepDurationForRate(rate_limits.search)
                print("Waiting {}s to reset the search timer of new token".format(sleep_time))
                sleep(sleep_time)
            else:
                print("Switched token")
    elif remaining_search < 2:
        sleep_time = computeSleepDurationForRate(rate_limits.search)
        print("Waiting {}s to reset the search timer".format(sleep_time))
        sleep(sleep_time)
                
    
        

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out

'''
Take a chunk of the undated commits and process them one by one, keep track
of how many have been updated to refresh the GitHub token
'''
def process_undated_commits_chunk(token_queue, chunk):
    
    print("Starting processing a chunk of size {}".format(len(chunk)))
    
    new_token = token_queue.get()    
    
    print("Using token {}".format(new_token))
    token_queue.put(new_token)    
    g = Github(new_token, per_page=100)
    
        
    
    
    mongo_client = MongoClient()
    
    database = mongo_client["graduation"]
    
    commits_collection = database["commits"]
    
    undated_commit_pointers_collection = database["undated_commit_pointers"]
    
    did = 0
    
    for undated_commit_pointer in chunk:
        date_undated_commit_pointer(undated_commit_pointer, g, commits_collection,
                                     undated_commit_pointers_collection)
        
        did += 1
        
        if did % 20:
            check_header_and_refresh(g, token_queue)

def date_undated_commit_pointer(commit_pointer, github, commits_collection, 
                                undated_commits_collection):
    sha = commit_pointer["sha"]
    owner = commit_pointer["project_owner"]
    name = commit_pointer["project_name"]
    
    query_string = "type:pr repo:{}/{} SHA:{}".format(
            owner, name, sha)
    
    res = github.search_issues(query_string)
    
    extracted_el = True
    
    try:
        tmp = res[0]
    except:
        extracted_el= False
    
    if not extracted_el:
        print("Could not find pull request for {}/{} number {}".format(
                owner,name, commit_pointer["pr_number"]))
    else:
        pr = res[0].as_pull_request()
        
        commits = pr.get_commits()
        
        updated = False
        
        for commit in commits:
            if commit.sha == sha:
                actual_date = commit.commit.author.date
                
                undated_commit = commits_collection.find_one({'sha':sha})
                
                undated_commit["date"] = actual_date
                
                commits_collection.replace_one({'_id':undated_commit['_id']}, undated_commit)
                
                undated_commits_collection.delete_one({"_id":commit_pointer["_id"]})
                
                updated = True
                
                print("Updated commit")
                
        if not updated:
            print("Could not update commit")



mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

undated_commit_pointers_collection = database["undated_commit_pointers"]

undated_commits = list(undated_commit_pointers_collection.find())

undated_commit_chunks = chunkIt(undated_commits, 4)

print("Loaded and chunked the commit list")

import multiprocessing
from functools import partial
    
    

token_queue = gh_tokens.gh_tokens    

m = multiprocessing.Manager()

shared_token_queue = m.Queue()

for token in IterableQueue(token_queue):
    shared_token_queue.put(token)

with multiprocessing.Pool(4) as p:
    func = partial(process_undated_commits_chunk, shared_token_queue)
    p.map(func, undated_commit_chunks)
