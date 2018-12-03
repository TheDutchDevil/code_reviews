# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 13:52:21 2018

Uses GHTorrent to find the created time for a scraped commit that has been
scraped without date. 

@author: natha
"""

'''
Update the date of commits for which no date exists. 
'''

from threading import Thread
from time import sleep

def update_function():
    while True:
        mc = MongoClient()

        db = mc["graduation"]
        
        cc = db["commits"]
        
        total = cc.count()
        todo = cc.find({'date':{'$exists':False}}).count()
        done = cc.find({'date':{'$exists':True}}).count()
        
        print("{}% is dated, {}% is left".format(done/total*100,todo/total*100))
        
        sleep(10)

import MySQLdb

from pymongo import MongoClient
from commit_dal import CommitDal

print("Starting date backscrape")
 
def resolve_ghtorrent_project_id(owner, name):
    db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")
    
    c = db.cursor()
    
    c.execute("""select proj.id
                    from projects proj, users user 
                    where proj.name = '{}'
                        and proj.owner_id = user.id 
                        and user.login = '{}' """.format(name,owner))
    
    res = c.fetchone()
    
    if res is None:
        return None
    else:
        return res[0]

thread = Thread(target = update_function)
#thread.start()

mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

commits_collection = database["commits"]

db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")
    
c = db.cursor()

done_projects = 0
failed_projects = 0

total_prs = 0
total_missed_prs_in_gh = 0
            
missing_in_data = 0
missing_in_ght = 0
commits_done = 0

projects_with_missing_prs = []

for project in list(projects_collection.find({'travis_is_oldest_ci':True}))[:1]:
    owner = project["full_name"].split("/")[0]
    name = project["full_name"].split("/")[1]
        
    gh_project_id = resolve_ghtorrent_project_id(owner, name)
    
    if gh_project_id is None:
        failed_projects += 1
        print("Failed {}".format(project["full_name"]))
        continue
    
    all_prs = list(pull_requests_collection.find(
        {
                'project_name': name, 
                'project_owner': owner
                }
        ).sort([('created_at', 1)]))
    
    pr_numbers = [pr["number"] for pr in all_prs]
    
    c.execute("select issue_id, pull_request_id from issues where repo_id = {} and pull_request = 1".format(gh_project_id))
    
    gh_pr_numbers = []
    pr_number_to_id ={}
    
    for row in c:
        gh_pr_numbers.append(row[0])
        pr_number_to_id[row[0]] = row[1]
    
    
    intersection_res = list(set(pr_numbers) & set(gh_pr_numbers))
    
    missing_in_gh = len(pr_numbers) - len(intersection_res)
    
    missing_in_mongo= len(gh_pr_numbers) - len(intersection_res)
    
    total_prs += len(all_prs)
    total_missed_prs_in_gh += missing_in_gh
    
    done_projects += 1
    
    if missing_in_gh > 0:
        projects_with_missing_prs.append(project)
        
    for pr_number in intersection_res:
        pull_request_id = pr_number_to_id[pr_number]
        
        pull_request = [pr for pr in all_prs if pr["number"] == pr_number][0]
        
        c.execute("select commit_id from pull_request_commits where pull_request_id = {}".format(pull_request_id))
        
        commit_ids = []
        
        for row in c:
            commit_ids.append(row[0])
            
        for commit_id in commit_ids:
            c.execute("select sha, created_at from commits where id = {}".format(commit_id))
            
            result= c.fetchone()
            
            if result[0] in pull_request["commits"]:
                pull_request["commits"].remove(result[0])
                
                commit = commits_collection.find_one({'sha':result[0]})
                
                if commit is not None:
                    commit["date"] = result[1]
                    
                    commits_done += 1
                    
                    commits_collection.replace_one({'_id':commit['_id']}, commit)
                    
                else:
                    missing_in_data += 1
                
        missing_in_ght += len(pull_request["commits"])
    
    
    
print("Did {} projects, {} failed".format(done_projects, failed_projects))
print("Out of a total of {} prs, we could not find {}".
      format(total_prs, total_missed_prs_in_gh))

print("There are {} projects that miss PRs in ght".format(len(projects_with_missing_prs)))

print("We did not scrape {} commits, and ght did not contain {} commits, total of the commits that has been updated is {}".
      format(missing_in_data, missing_in_ght, commits_done))

exit(0)