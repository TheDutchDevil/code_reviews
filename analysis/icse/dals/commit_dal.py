# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 13:29:07 2018

@author: natha
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 14:16:20 2018

@author: natha
"""

from pymongo import MongoClient

class CommitDal:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["graduation"]
        self.collection = self.db["commits"]
        
    def count_commits(self):
        return self.collection.estimated_document_count()

    
    def insert_commits(self, commits):
        try:
            for commit in commits:
                self.collection.insert(commit)
        except Exception as e:
            print("Failed inserting commit {} with url {}, error: {}".format(commit["commit_sha"], commit["html_url"], e))
            raise e
        