# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 12:41:03 2018

@author: natha
"""

# Process all pull requests in the dataset and run them through the ngramizer. 
# After generating the bigrams, these are stored in mongodb instance. 

import analysis.ngramizer as ngramizer

from pymongo import MongoClient
from collections import Counter

def ngramize_project_prs(project):  
    
    ngram_length = 2
    
    mongo_client = MongoClient()
    
    database = mongo_client["graduation"]
    
    pull_requests_collection = database["pull_requests"]
    
    print("Doing {}".format(project["full_name"]))
    
    prs = list(pull_requests_collection.find(
            { 
                    'project_name': project["full_name"].split("/")[1],
                    'project_owner': project["full_name"].split("/")[0]
            }))   
            
    usernames = []
    
    for pr in prs:
        
        usernames.extend(ngramizer.given_text_extract_usernames(pr["body"]))
        
        usernames.append(pr["user"]["login"])
        
        for comment in pr["raw_comments"]:
            usernames.extend(ngramizer.given_text_extract_usernames(
                                    comment["body"]))
            
            usernames.append(comment["user"]["login"])
            
        for comment in pr["review_comments"]:
            usernames.extend(ngramizer.given_text_extract_usernames(
                                    comment["body"]))
            
            if comment["user"] is not None:
               usernames.append(comment["user"]["login"])
                       
    usernames = list(set(usernames))
            
    project["usernames"] = usernames    
    
    for pr in prs:
        #if not ngramizer.is_bot_comment(pr["user"]["login"]):
            
		body_counter = Counter()
		
		ngramizer.add_text_ngrams_to_counter(pr["body"], 
											 pr.get("html_url", ""), 
											 ngram_length, 
											 body_counter, 
											 {}, 
											 project["usernames"]
											 )
		
		pr["bigrams"] = []
		
		for item in body_counter:
			bigram_result = {
				'bigram':[item[0], item[1]],
				'occurrence': body_counter[item]
			}
			
			pr['bigrams'].append(bigram_result)
                
                
        
        for comment in pr["raw_comments"]:
            #if not ngramizer.is_bot_comment(comment["user"]["login"]):
                
			comment_counter = Counter()
			
			ngramizer.add_text_ngrams_to_counter(comment["body"], 
												 comment.get(
														 "html_url", ""
														 ), 
												 ngram_length, 
												 comment_counter, 
												 {}, 
												 project["usernames"]
												 )
			comment["bigrams"] = []
							 
			for item in comment_counter:
				bigram_result = {
				'bigram':[item[0], item[1]],
				'occurrence': comment_counter[item]
				}
			
				comment['bigrams'].append(bigram_result)
                    
        for comment in pr["review_comments"]:
            if comment["user"] is not None #and \
                #not ngramizer.is_bot_comment(comment["user"]["login"]):
                
                comment_counter = Counter()
                
                ngramizer.add_text_ngrams_to_counter(comment["body"], 
                                                     comment.get(
                                                             "url", ""
                                                             ), 
                                                     ngram_length, 
                                                     comment_counter, 
                                                     {}, 
                                                     project["usernames"]
                                                     )
                comment["bigrams"] = []
                                 
                for item in comment_counter:
                    bigram_result = {
                    'bigram':[item[0], item[1]],
                    'occurrence': comment_counter[item]
                    }
                
                    comment['bigrams'].append(bigram_result)
                    
        
        pull_requests_collection.replace_one({"_id":pr["_id"]}, pr)
               
# Run this multithreaded with 8 threads
        
mongo_client = MongoClient()

database = mongo_client["graduation"]

projects_collection = database["projects"]

projects = list(projects_collection.find({'succeeded' : True, 'travis_is_oldest_ci': True}))

import multiprocessing

with multiprocessing.Pool(8) as p:
    p.map(ngramize_project_prs, projects)