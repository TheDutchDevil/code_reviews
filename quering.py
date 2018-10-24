# -*- coding: utf-8 -*-
"""
A script containing some advanced queries used to find specific samples to
explore. 

Created on Tue Oct 23 12:45:44 2018

@author: natha
"""

#%%

"""
Find projects that have a large number of outsider contributions, then list 
active users contributing to the project, together with their insider vs
outsider status. 
"""
from pymongo import MongoClient

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

projects = list(projects_collection.find({'succeeded' : True, 
                                          'travis_is_oldest_ci': True}))

outsider_projects = []

for project in projects:
    
    prs = list(pull_requests_collection.find(
            {
                    'project_name': project["full_name"].split("/")[1],
                    'project_owner': project["full_name"].split("/")[0]
                    }
            ))
        
    if len(prs) < 200:
        continue
    
    # Do shares outsider
    
    total_outsider = sum([1 for pr in prs if pr["from_outsider"]])      
        
    total_insider = sum([1 for pr in prs if not pr["from_outsider"]])
        
    if total_outsider == 0 or total_insider == 0:
        continue
    
    shares_outsider = total_outsider / (total_outsider + total_insider)
    
    if shares_outsider > .8:
        outsider_projects.append(project)

#%%

for project in outsider_projects:
    # Dictionary containing one entry per user, the entry is a tuple of
    # (insider, outsider) where the entry counts the number of PRs opened by
    # the user. 
    users = {}
    
    prs = list(pull_requests_collection.find(
            {
                    'project_name': project["full_name"].split("/")[1],
                    'project_owner': project["full_name"].split("/")[0]
                    }
            ))
    
    for pr in prs:
        username = pr["user"]["login"]
        if username not in users:
            users[username] = {"insider": 0, "outsider": 0}
            
        if pr["from_outsider"]:
            users[username]["outsider"] += 1
        else:
            users[username]["insider"] += 1
            
    take = 10
            
    print("{} most active users for {} are".format(take, project["full_name"]))
            
    for user in sorted(users, 
                       key = lambda user: users[user]["insider"] + users[user]["outsider"])[-take:]:
        print("\t{}: ({}/{})".format(user, users[user]["insider"], users[user]["outsider"]))
            
