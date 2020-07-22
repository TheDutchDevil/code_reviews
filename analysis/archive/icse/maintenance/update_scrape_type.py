# We have the problem that a project might be scraped for several reason,
# therefore we have to upgrade the scrape_type to be an array instead of
# a field.
#
# Secondly do we need to use the existing list of scraped projects to add
# elements to the array.

from pymongo import MongoClient

mongo_client = MongoClient()
database = mongo_client["graduation"]
pull_requests_collection = database["pull_requests"]
projects_collection = database["projects"]
commits_collection = database["commits"]

projects = projects_collection.find()

for project in projects:
    if "scrape_type" in project:
        project["scrape_type"] = [project["scrape_type"]]
    else:
        project["scrape_type"] = ["travis_1"]

    projects_collection.replace_one({"_id": project["_id"]}, project)


import csv

with open('../scraping/circle_projects_to_scrape.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        if line_count > 0:
            project = projects_collection.find_one({'full_name': row["Slug"]})

            if not project is None:
                if not "icse_1" in project["scrape_type"]:
                    project["scrape_type"].append("icse_1")

                    projects_collection.replace_one({"_id": project["_id"]}, project)

                    print("updated {}".format(row["Slug"]))
        line_count += 1
    print(f'Processed {line_count} lines.')

