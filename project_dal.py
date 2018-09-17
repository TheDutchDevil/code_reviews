from pymongo import MongoClient

class ProjectDal:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["graduation"]
        self.collection = self.db["projects"]
        
    def count_projects(self):
        return self.collection.estimated_document_count()
    
    def project_inserted(self, slug):
        return self.project_for_slug(slug) is not None
        
    def project_for_slug(self, slug):
        project = self.collection.find_one({'slug': slug})
        
        return project
    
    def insert_project(self, project):
        self.collection.insert_one(project)