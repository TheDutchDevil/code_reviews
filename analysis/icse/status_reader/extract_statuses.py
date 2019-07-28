from pymongo import MongoClient
from urllib.parse import urlparse
from collections import Counter


mongo_client = MongoClient()
database = mongo_client["graduation"]
pull_requests_collection = database["pull_requests"]
projects_collection = database["projects"]
commits_collection = database["commits"]

project_slugs = list(projects_collection.find({'succeeded': True}))


for project in project_slugs:

    pull_requests = list(pull_requests_collection.find({'project_name': project["full_name"].split("/")[1],
                                                       'project_owner': project["full_name"].split("/")[0]},
                                                      {'commits':1, 'raw_comments':1, 'created_at': 1}))
        
    sha_list = list([commit for pr in pull_requests for commit in pr["commits"]])
        
    commits = [commits_collection.find_one({'sha': sha_hash}, {'statuses': 1}) for sha_hash in sha_list]

    statuses = list([status for commit in commits for status in commit["statuses"]])

    ci_services = []

    # We need atleast one commit status to do some work.
    if len(statuses) > 0:       
        all_urls = [status["target_url"] for status in statuses]       
        
        hostnames = list([urlparse(url).hostname for url in all_urls if urlparse(url).hostname is not None])

        hostnames_counter = Counter(hostnames)

        popular_hosts = []

        for val in hostnames_counter:
            if hostnames_counter[val] >= 10:
                if not val in popular_hosts:
                    popular_hosts.append(val)

        for host in popular_hosts:
            host_statuses = [status for status in statuses if urlparse(status["target_url"]).hostname == host]

            oldest_status = min([status["created_at"] for status in host_statuses])

            ci_services.append({"host": host, "introduced": oldest_status, "count": len(host_statuses)})

    project["services"] = ci_services

    projects_collection.replace_one({"_id": project["_id"]}, project)
