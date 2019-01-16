'''
Script used to verify the commit dates scraped by scraper, to try and find projects
or instances of wrongly scraped commit dates
'''

import gh_tokens

from time import sleep
import datetime
from math import ceil

import random


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
                print("Waiting 60s to reset the search timer of new token")
                sleep(60)
            else:
                print("Switched token")
    elif remaining_search < 2:
        sleep_time = computeSleepDurationForRate(rate_limits.search)
        print("Waiting {}s to reset the search timer".format(60))
        sleep(60)

unmatched = 0
wrong_date = 0
right_date = 0

from github import Github

token_queue = gh_tokens.gh_tokens 

new_token = token_queue.get()    
    
token_queue.put(new_token)    

g = Github(new_token, per_page=100)

from pymongo import MongoClient
from bson.objectid import ObjectId

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]
projects = list(projects_collection.find({'succeeded' : True, 'travis_is_oldest_ci': True}))

wrong_projs = []

for project in projects:
    prs = list(pull_requests_collection.find({'project_owner':project["full_name"].split("/")[0], 'project_name':project["full_name"].split("/")[1]}))

    for pr in random.sample(prs, 10):

        check_header_and_refresh(g, token_queue)

        full_commits = list([commits_collection.find_one({'sha': commit_hash}) for commit_hash in pr["commits"]])

        query_string = "type:pr repo:{}/{} SHA:{}".format(
            project["full_name"].split("/")[0] , project["full_name"].split("/")[1], pr["commits"][0])
    
        res = g.search_issues(query_string)

        extracted_el = True

        try:
            tmp = res[0]
        except:
            extracted_el= False
        
        if not extracted_el:
            print("Could not find pull request for {}".format(project["full_name"]))
            break

        pr = res[0].as_pull_request()
        
        commits = pr.get_commits()

        for commit in commits:
            matching = [cmt for cmt in full_commits if cmt["sha"] == commit.sha and 'date' in cmt]

            if len(matching) != 1:
                unmatched += 1
            elif commit.commit.author.date != matching[0]["date"]:
                wrong_date += 1
            else:
                right_date += 1
            
        print("unmatched: {}, right {}, wrong {}. {}% is unmatched, {}% is wrong".format(
            unmatched, right_date, wrong_date, unmatched / (unmatched +right_date+wrong_date) * 100,
            wrong_date / (right_date + wrong_date) * 100
        ))

