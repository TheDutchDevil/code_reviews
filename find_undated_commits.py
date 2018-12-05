# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 13:44:01 2018

Script that finds commits in the dataset that do not have a dated. Stores
their hashes in a different collection, together with project and 
pull request information.

@author: natha
"""

from pymongo import MongoClient

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

undated_commit_pointers_collection = database["undated_commit_pointers"]

for project in list(projects_collection.find({'travis_is_oldest_ci':True})):
    owner = project["full_name"].split("/")[0]
    name = project["full_name"].split("/")[1]
        
    
    all_prs = list(pull_requests_collection.find(
        {
                'project_name': name, 
                'project_owner': owner
                }
        ).sort([('created_at', 1)]))
    
    
        
    for pr in all_prs:
        for commit_hash in pr["commits"]:
            commit = commits_collection.find_one({"sha" : commit_hash})
            
            if "date" not in commit:
                commit_pointer = {'sha': commit_hash, 
                 'project_name' : name,
                 'project_owner': owner,
                 'pr_number': pr["number"]}
                
                if undated_commit_pointers_collection.find({'sha': commit_hash}).count() == 0:
                
                    undated_commit_pointers_collection.insert_one(commit_pointer)
                
    print("Analyzed {}".format(project["full_name"]))

