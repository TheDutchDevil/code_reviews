from pymongo import MongoClient
from pull_request_dal import PullRequestDal

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
        project = self.collection.find_one({'full_name': slug})
        
        return project
    
    def insert_project(self, project):
        self.collection.insert_one(project)

    def delete_project(self, slug):

        project = self.collection.find_one({"full_name": slug}, {"_id": 1})

        if project is None:
            raise ValueError("Project not found")

        project_name = slug.split("/")[1]
        project_owner = slug.split("/")[0]

        pull_requests = self.db["pull_requests"].find({"project_name": project_name, "project_owner": project_owner}, {"_id": 1})

        prDal = PullRequestDal()

        for pr in pull_requests:
            prDal.delete_pull_request(pr["_id"])

        self.collection.delete_one({"_id": project["_id"]})
    
    def find_projects(self, search, projection):
        return self.collection.find(search, projection)
