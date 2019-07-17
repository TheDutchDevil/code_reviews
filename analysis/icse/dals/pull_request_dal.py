# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 14:16:20 2018

@author: natha
"""

from pymongo import MongoClient

from commit_dal import CommitDal

class PullRequestDal:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["graduation"]
        self.collection = self.db["pull_requests"]
        
    def count_pull_requests(self):
        return self.collection.estimated_document_count()

    
    def insert_pull_requests(self, pull_requests):
        try:
            for pr in pull_requests:
                self.collection.insert(pr)
        except Exception as e:
            print("Failed inserting PR {} with url {}, error: {}".format(pr["number"], pr["html_url"], e))
            raise e
        
    def delete_pull_request(self, id):
        pr = self.collection.find_one({"_id": id}, {"commits": 1})

        commitDal = CommitDal()

        for hash in pr["commits"]:
            commitDal.delete_commit(hash)

        self.collection.delete_one({"_id": pr["_id"]})