# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 14:18:38 2018

@author: natha
"""

from pymongo import MongoClient

class IssueDal:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["graduation"]
        self.collection = self.db["issues"]
        
    def count_issues(self):
        return self.collection.estimated_document_count()

    
    def insert_issues(self, issues):
        if len(issues) > 0:
            self.collection.insert_many(issues)