# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 14:58:01 2018

@author: natha
"""
import pandas as pd
import MySQLdb

import scrape_projects_from_github as scraper

BOGDAN_DATASET_NAME = "../data/active_repos_v2_bogdan.csv"

db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")

c = db.cursor()

bogdan_data = pd.read_csv(BOGDAN_DATASET_NAME, sep=",")


#%%
import json
import os
from bson import json_util



ase_repos = bogdan_data['slug']

print("Total of {} repos".format(len(ase_repos)))

found_projects = []

if not os.path.exists("../data/travis_projects_with_comments_bogdan.json"):

    for slug in ase_repos:
        res = scraper.project_has_more_than_1000_comments(slug, c)
        if res is not None:
            found_projects.append(res)
            print(found_projects[-1])


    with open('../data/travis_projects_with_comments_bogdan.json', 'w') as fp:
        json.dump(found_projects, fp, sort_keys=True, indent=4,  default=json_util.default)
        
else:
    with open('../data/travis_projects_with_comments_bogdan.json', 'r') as fp:
        found_projects = json.load(fp)
        
print("found {} projects".format(len(found_projects)))

scraper.execute_scrape_list(found_projects)
