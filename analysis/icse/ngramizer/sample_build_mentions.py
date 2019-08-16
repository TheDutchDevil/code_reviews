from pymongo import MongoClient

import random

import csv

mongo_client = MongoClient()
database = mongo_client["graduation"]

mentions_collection = database["mentions"]

mentions = list(mentions_collection.find({}, {'_id': 0, 'type': 0}))

sample = random.sample(mentions, 1000)

with open('build_mentions_sample.csv', mode='w', encoding="utf-8") as csv_file:
    fieldnames = ['identifier', 'sentence', 'url']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for item in sample:
        writer.writerow(item)
