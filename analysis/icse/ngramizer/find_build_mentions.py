'''
Given a dataset, extract all sentences using the following words.
'''

from ngramizer import *

from pymongo import MongoClient

mongo_client = MongoClient()
database = mongo_client["graduation"]
pull_requests_collection = database["pull_requests"]
projects_collection = database["projects"]
commits_collection = database["commits"]

projects = list(projects_collection.find({'scrape_type':'travis_1', 'succeeded': True}))

for project in projects:
    name = project["full_name"].split("/")[1]
    owner = project["full_name"].split("/")[0]

    for pr in list(pull_requests_collection.find({
        'project_name':name,
        'project_owner':owner
    }, {
        'bigrams':0,
        'raw_comments.bigrams':0,
        'review_comments':0
    })):
        nr_comment = 0

        for comment in pr["raw_comments"]:
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

                if "build" in sentence_l or \
                    "continuous" in sentence_l or \
                    "integration" in sentence_l or \
                    "travis" in sentence_l:
                    location = "{}.{}.{}.{}".format(project["full_name"],
                                            pr["number"],
                                            nr_comment,
                                            line)

                    mention_found = {
                        "identifier":location,
                        "sentence" : sentence,
                        "url" : comment["html_url"]
                    }

                    print(mention_found)

                line += 1
            nr_comment += 1

