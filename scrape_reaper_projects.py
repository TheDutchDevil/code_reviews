# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 14:58:01 2018

@author: natha
"""
import pandas as pd
import MySQLdb

import scrape_projects_from_github as scraper

REAPER_DATASET_NAME = "../data/utility.csv"

db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")

c = db.cursor()

reaper_data = pd.read_csv(REAPER_DATASET_NAME, sep=",")

# This mimics the selection done in the Travis script for the ASE paper. 
reaper_project_data = reaper_data[reaper_data["class"] == "project"]

reaper_project_data["slugs"] = reaper_project_data["github_url"].str.replace("https://github.com/", "")


#%%
import json
import os

import json_util

ase_repos = reaper_project_data['slugs']

print("Total of {} repos".format(len(ase_repos)))

found_projects = []

if not os.path.exists("../data/travis_projects_with_comments_reaper.json"):

    for slug in ase_repos:
        res = scraper.project_has_more_than_1000_comments(slug, c)
        if res is not None:
            found_projects.append(res)
            print(found_projects[-1])


    with open('../data/travis_projects_with_comments_reaper.json', 'w') as fp:
        json.dump(found_projects, fp, sort_keys=True, indent=4,  default=json_util.default)
        
else:
    with open('../data/travis_projects_with_comments_reaper.json', 'r') as fp:
        found_projects = json.load(fp)
        
print("found {} projects".format(len(found_projects)))

scraper.execute_scrape_list(found_projects)