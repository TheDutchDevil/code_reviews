# -*- coding: utf-8 -*-
"""
This script moves all existing commits belonging to pull requests to their
own collection. 

In addition to that another cell in this script can be used to clear dangling
pull requests. 

Created on Sat Sep 29 13:44:27 2018

@author: natha
"""

# Move commits from PRs to their own collection

from pymongo import MongoClient
from commit_dal import CommitDal

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commit_dal = CommitDal()

for pr in pull_requests_collection.find( {"$and": [
        {"commits": { "$exists": True, "$not": {"$size": 0} }}, 
        {"commits.sha": { "$exists":True}}
        ]}):
    
    for commit in pr["commits"]:
        commit["project_name"] = pr["project_name"]
        commit["project_owner"] = pr["project_owner"]
    
    commit_dal.insert_commits(pr["commits"])
    
    pr["commits"] = [commit["sha"] for commit in pr["commits"]]
    
    pull_requests_collection.replace_one({"_id":pr["_id"]}, pr)
    
#%%
    
# Delete all data of failed projects    

from pymongo import MongoClient
from commit_dal import CommitDal

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

for failed_project in projects_collection.find({'succeeded': False}):
    print("Deleting {}".format(failed_project["full_name"]))
    split_name = failed_project["full_name"].split("/")
    
    for pr in pull_requests_collection.find({'project_name':
        split_name[1], 'project_owner':
            split_name[0]}):
        for sha in pr["commits"]:
            commits_collection.delete_one({'sha':sha})
    
    pull_requests_collection.delete_many({'project_name':
        split_name[1], 'project_owner':
            split_name[0]})
    
    projects_collection.delete_one({'full_name':failed_project["full_name"]})
    
#%%
    
# Attribute each PR with a boolean, whether they were opened by insiders or
# outsiders. An insider is someone who merged a PR that was not his own, e.g.
# someone who has merge rights on a repository. 

from pymongo import MongoClient
from commit_dal import CommitDal

import multiprocessing

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

projects = list(projects_collection.find({'travis_is_oldest_ci' : True}))

def do_insiders_for_project(project):
    print("Analyzing: {}".format(project["full_name"]))
    
    split_name = project["full_name"].split("/")
    
    all_prs_done_count = pull_requests_collection.find(
            {
                    'project_name': split_name[1], 
                    'project_owner': split_name[0],
                    'from_outsider': {'$exists':True}
                    }).count()
        
    all_prs = list(pull_requests_collection.find(
            {
                    'project_name': split_name[1], 
                    'project_owner': split_name[0]
                    }
            ).sort([('created_at', 1)]))
    
    if all_prs_done_count == len(all_prs):
        return
    
    insiders = []
    
    for pr in all_prs:
    
        contributor = pr["user"]["login"]
        
        pr["from_outsider"] = not (contributor in insiders)
        
        if "merged_by" in pr and pr["merged_by"] is not None:
            
            closer = pr["merged_by"]["login"]
            
            if contributor != closer:
                insiders.append(closer)
        
            
        pull_requests_collection.replace_one({"_id":pr["_id"]}, pr)
        
 
for project in projects:
    do_insiders_for_project(project)

    
    