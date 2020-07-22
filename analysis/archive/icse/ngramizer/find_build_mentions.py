'''
Given a dataset, extract all sentences using the following words.
'''

from ngramizer import *

from pymongo import MongoClient

'''

Used for first batch

terms = [
    "build",
    "continuous",
    "integration",
    "travis",
    "lint",

]

tag = "ci_mention"
'''

terms = [
    "success",
    "failure",
    "build",
    "status",
    "check",
    "pass",
    "fail",
    "travis"
]

tag="ci_mention_extended"

mongo_client = MongoClient()
database = mongo_client["graduation"]
pull_requests_collection = database["pull_requests"]
projects_collection = database["projects"]
commits_collection = database["commits"]

mentions_collection = database["mentions"]

projects = list(projects_collection.find({'scrape_type':'travis_1', 'succeeded': True, 'travis_is_oldest_ci': True}))

for project in projects:
    name = project["full_name"].split("/")[1]
    owner = project["full_name"].split("/")[0]

    for pr in list(pull_requests_collection.find({
        'project_name':name,
        'project_owner':owner,
        'created_at': { '$gt' : project["status_travis_date"]}
    }, {
        'bigrams':0,
        'raw_comments.bigrams':0,
        'review_comments':0
    })):
        nr_comment = 0

        for comment in pr["raw_comments"]:
            if "body" not in comment or \
                comment["body"] is None:
                nr_comment += 1
                continue

            text = comment["body"]

            text = text.lower()

            '''
            First we clean, strip and tokenize the text
            '''
            cleaned_text = clean_text(text)

            tokenized_text = tokenize_text(cleaned_text, names = [])

            stripped_text = remove_markdown_content(tokenized_text)

            sentences = split_into_sentences(stripped_text)

            line = 0
            for sentence in sentences:
                
                sentence_l = sentence.lower()

                vals = [term in sentence_l for term in terms]

                if True in vals:
                    location = "{}.{}.{}.{}".format(project["full_name"],
                                            pr["number"],
                                            nr_comment,
                                            line)

                    mention_found = {
                        "identifier":location,
                        "sentence" : sentence,
                        "url" : comment["html_url"],
                        "type" : [tag]
                    }

                    mention_in_db = mentions_collection.find_one({ 
                        'identifier' : mention_found["identifier"]})

                    if mention_in_db is None:
                        mentions_collection.insert_one(mention_found)
                    else:
                        if not tag in mention_in_db["type"]:
                            mention_in_db["type"].append(tag)

                            mentions_collection.replace_one({'_id':mention_in_db["_id"]}, mention_in_db)

                line += 1
            nr_comment += 1

