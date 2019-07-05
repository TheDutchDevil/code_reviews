'''
Given a set of github projects that have enough activity
for an RDD analysis we verify whether these projects all
have at least one file making them CI projects. 

To do this we split the set of projects and we use as 
many threads as we have github tokens to search for the
presence of a file in the repository. 
'''

import csv
import tokens.gh_tokens as token
import multiprocessing
import datetime

from time import sleep
from math import ceil
from github import Github, GithubException

def get_projects():
    projects = []

    with open('longer2y_and_more24pr.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                projects.append({"Id": row[0], "Slug": row[1], "Url": row[2]})
            line_count += 1
    print("Read {} projects".format(len(projects)))
    return projects

def make_chunks(l, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield l[i::n]

def getRateLimit(g):
    return g.get_rate_limit().core

def getRateLimitSearch(g):
    return g.get_rate_limit().search


def computeSleepDuration(g):
    reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds()))

def computeSleepDurationForRate(rate):
    reset_time = rate.reset
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds())) -21590 + 7200


def waitIfDepleted(g):    
    rate_limit = getRateLimit(g)
    
    sleep_duration = computeSleepDuration(g)
    if not rate_limit.remaining > 49:
        print("Waiting {} minutes".format(sleep_duration/60)) + 7210
        sleep(sleep_duration)
    


def check_header_and_refresh(g):
    rate_limits = g.get_rate_limit()
    remaining_search = rate_limits.search.remaining
    remaining_core = rate_limits.core.remaining

    if remaining_search < 4:
        #sleep_time = computeSleepDurationForRate(rate_limits.search)
        #print("Waiting {}s to reset the search timer".format(60))
        sleep(60)
    if remaining_core < 20:
        print("Depleted the core request numbers")
        print("------------------------------")

def get_ci_for_project(project, found_projects):
            travis_files = g.search_code(base_query.format(project["Slug"], "travis.yml", "/"))

            has_travis = False

            for tr_file in travis_files:
                has_travis = True
                break

            circle_files = g.search_code(base_query.format(project["Slug"], "config.yml", ".circleci/"))

            has_circle = False

            for circle_file in circle_files:
                has_circle = True
                break

            project["HasTravis"] = has_travis
            project["HasCircle"] = has_circle

            found_projects.append(project)


def process_projects_chunk(args):
    projects, key = args[0], args[1]

    found_projects= []

    g = Github(key)

    base_query = "repo:{} filename:{} path:{}"

    for project in projects:
        try:
            check_header_and_refresh(g)

            get_ci_for_project(project, found_projects)
            
        except GithubException as e:
            if e.status == 403:
                print("Ran into rate limit, backing off")
                sleep(120)
                check_header_and_refresh(g)
                get_ci_for_project(project, found_projects)
            elif e.status != 422:
                raise e
            else:
                print("Could not find project {}".format(project["Slug"]))

    return found_projects

if __name__ == "__main__":
    projects = get_projects()

    chunks = make_chunks(projects, token.gh_tokens.qsize())

    data = ([(projects, token) for projects, token in zip(chunks, list(token.gh_tokens.queue))])

    calc_pool = multiprocessing.Pool(processes=token.gh_tokens.qsize())  

    print("Starting {} threads".format(token.gh_tokens.qsize()))

    # run our processes and await responses
    modified_projects = calc_pool.map(process_projects_chunk, data)

    modified_projects = [item for sublist in modified_projects for item in sublist]

    with open('longer2y_and_more24pr_withci.csv', mode='w', newline='') as csv_file:
        fieldnames = ['Id', 'Slug', 'Url', 'HasTravis', 'HasCircle']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        
        for project in modified_projects:
            writer.writerow(project)
