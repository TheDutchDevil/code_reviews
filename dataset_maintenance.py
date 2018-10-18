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

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

for project in projects_collection.find({'travis_is_oldest_ci' : True}):
    print("Analyzing: {}".format(project["full_name"]))
    
    split_name = project["full_name"].split("/")
    
    insiders = []
    
    for pr in pull_requests_collection.find({'project_name':
        split_name[1], 'project_owner':
            split_name[0], 
            'from_outsider' : {'$exists':False}}).sort([('created_at', 1)]):
    
        if "merged_by" in pr and pr["merged_by"] is not None:
            contributor = pr["user"]["login"]
            
            closer = pr["merged_by"]["login"]
            
            pr["from_outsider"] = contributor not in insiders
            
            if contributor != closer:
                insiders.append(closer)
        else:
            pr["from_outsider"] = False
            
        pull_requests_collection.replace_one({"_id":pr["_id"]}, pr)
        
#%%

# Process all pull requests in the dataset and run them through the ngramizer. 
# After generating the bigrams, these are stored in mongodb instance. 

import ngramizer






        