'''

File containing the analysis to determine what the impact is of the
fact that we're not mining pull request reviews, and only review 
comments. 

'''

from pymongo import MongoClient
from github import Github

# Init pygh class
g = Github("be8e00a57c90b5334d433e41d1cc1471254355b9")


# Init mongodb collections
mongo_client = MongoClient()

database = mongo_client["graduation"]

pull_requests_collection = database["pull_requests"]

projects_collection = database["projects"]

projects = list(projects_collection.find({'travis_is_oldest_ci' : True}))

for project in projects:
    
    split_name = project["full_name"].split("/")
    
    prs = list(pull_requests_collection.find({'project_name':
        split_name[1], 'project_owner':
            split_name[0]}).sort([('created_at',-1)]))
    
    prs_with_review_comments = len([pr for pr in prs if len(pr["review_comments"]) > 0])
    
    share_with_review_comments = prs_with_review_comments / len(prs)
    
    print("{}: {}%".format(project["full_name"], share_with_review_comments * 100))
    
    if share_with_review_comments < 0.5 and project["full_name"] != "OCA/bank-payment":
        continue
        
    pgh_project = g.get_repo(project["full_name"])
    
    for pr in prs:
        pgh_pr = pgh_project.get_pull(pr["number"])
        
        print(pr["number"])
        
        nr_review_comments = len(pr["review_comments"])
        
        nr_gh_review = 0
        
        for pgh_review in pgh_pr.get_reviews():
            nr_gh_review += 1
        
        if nr_gh_review is None:
            print("no review found")
            nr_gh_review = 0
        
        if nr_gh_review > nr_review_comments:
            print("you fail")
            
        print("{}/{}".format(nr_gh_review, nr_review_comments))

#%%