'''

Script used to find a specific PR that has been squash merged. This script
then counts the number of commits found through the pull request API. If this
number is 2, then that means we still find the original PRs that are squashed
by doing a squash merge.

'''

from json import JSONEncoder
from time import sleep

import github
import gh_tokens
import datetime
import traceback

from github import Github
from math import ceil
from pymongo import MongoClient

import queue



if __name__ == "__main__":
    print("finding single pR")
    mongo_client = MongoClient()

    database = mongo_client["graduation"]

    pull_requests_collection = database["pull_requests"]

    projects_collection = database["projects"]

    commits_collection = database["commits"]
    

    token_queue = gh_tokens.gh_tokens 

    
    g = Github(per_page=100)  

    try:
        query_string = "type:pr repo:{}/{} SHA:{}".format(
                "TheDutchDevil", "code_reviews", "71a7c41ba89edf7caa6ea24713c71f389119b696")
        
        res = g.search_issues(query_string)
        
        extracted_el = True
        
        try:
            tmp = res[0]
        except:
            extracted_el= False
        
        if not extracted_el:
            print("Could not find pr")
        else:
            for found_pr in res:
                if found_pr.number == 2:
                    gh_pr = found_pr.as_pull_request()

                                
                    commits = gh_pr.get_commits()

                    for commit in commits:
                        print(commit.sha)

                    
    except Exception as e:
        print(e)
