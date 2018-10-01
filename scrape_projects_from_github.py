import pandas as pd
import MySQLdb

ASE_DATASET_NAME = "../data/travis_adoption_metrics_md5.csv"

db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")

c = db.cursor()

ase_data = pd.read_csv(ASE_DATASET_NAME, sep=";")

ase_data.head()

# This mimics the selection done in the Travis script for the ASE paper. 

merge_data = ase_data.loc[ase_data["period"] != 0].groupby(['Repo'], as_index=False)[['num_merge_commits', 'num_non_merge_commits']].min().query('num_merge_commits > 0 & num_non_merge_commits > 0')

merge_data.head()

#%%

import json
import os

ase_repos = merge_data['Repo']

print("Total of {} repos".format(len(ase_repos)))

found_projects = []

if not os.path.exists("../data/travis_projects_with_comments.json"):

    for slug in ase_repos:
        split = slug.split("/")

        username = split[0]
        reponame = split[1]

        c.execute("""select proj.id, proj.language
                        from projects proj, users user 
                        where proj.name = '{}'
                            and proj.owner_id = user.id 
                            and user.login = '{}' 
                            and total_number_pr_comments > 1000""".format(reponame, username))

        res = c.fetchone()

        if res is not None:
            found_projects.append({'slug': slug, 'id': res[0], 'lang': res[1]})
            print(found_projects[-1])


    with open('../data/travis_projects_with_comments.json', 'w') as fp:
        json.dump(found_projects, fp, sort_keys=True, indent=4,  default=json_util.default)
        
else:
    with open('../data/travis_projects_with_comments.json', 'r') as fp:
        found_projects = json.load(fp)
        
print("found {} projects".format(len(found_projects)))

#%%

from json import JSONEncoder
from time import sleep

import github

class GitHubEncoder(JSONEncoder):
    
    def default(self, o):
        if o is github.GithubObject.NotSet:
            return None
        elif isinstance(o, github.Requester.Requester):
            return o.__dict__
        elif isinstance(o, HTTPSRequestsConnectionClass):
            return None
                
        return json.JSONEncoder.default(self, o)
                

def getRateLimit(g):
    return g.get_rate_limit().core


def computeSleepDuration(g):
    reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds()))


def waitIfDepleted(g):    
    rate_limit = getRateLimit(g)
    
    sleep_duration = computeSleepDuration(g)
    if not rate_limit.remaining > 55:
        sleep(sleep_duration)
    

def waitAndGetRepo(g, slug):
    waitIfDepleted(g)
    return g.get_repo(slug)

def check_header_and_refresh(g, token_queue):
    remaining = g.get_rate_limit().core.remaining

    if remaining < 50:
        if token_queue.qsize() == 1:
            print("Only one token so waiting")
            waitIfDepleted(g)
        else:        
            new_token = token_queue.get()
            token_queue.put(new_token)
            g._Github__requester._Requester__authorizationHeader = "token " + new_token
            
            remaining = g.get_rate_limit().core.remaining
            
            if remaining < 50:
                print("New token is depleted, so waiting")
                waitIfDepleted(g)
                print("Done waiting")
            else:
                print("Switched token")
        
    
print(github.Requester.Requester)

#%%

def parse_named_user(user):
    if user is None:
        return None
    else:
        return {
            'login': user.login,
            'html_url': user.html_url,
            'url' : user.url
        }

def parse_repo(repo):
    return {
        'created_at':repo.created_at,
        'description': repo.description,
        'fork': repo.fork,
        'forks': repo.forks,
        'full_name': repo.full_name,
        'id': repo.id,
        'language': repo.language,
        'name': repo.name,
        'owner': parse_named_user(repo.owner),
        'size': repo.size,
        'stargazers_count': repo.stargazers_count,
        'subscribers_count': repo.subscribers_count,
        #'topics': repo.topics,
        'watchers': repo.watchers,
        'html_url': repo.html_url,
        'url': repo.url
    }

def parse_pull_request(pull_request):
    return {
        'additions': pull_request.additions,
        'assignee': parse_named_user(pull_request.assignee),
        'assignees': [parse_named_user(assignee) for assignee in pull_request.assignees],
        'body': pull_request.body,
        'changed_files': pull_request.changed_files,
        'closed_at': pull_request.closed_at,
        'commits': pull_request.commits,
        'created_at': pull_request.created_at,
        'deletions': pull_request.deletions,
        'id': pull_request.id,
        'merged': pull_request.merged,
        'merged_at': pull_request.merged_at,
        'merged_by': parse_named_user(pull_request.merged_by),
        'number': pull_request.number,
        'state': pull_request.state,
        'title': pull_request.title,
        'updated_at': pull_request.updated_at,
        'user': parse_named_user(pull_request.user),
        'html_url': pull_request.html_url,
        'url': pull_request.url
    }

def parse_issue(issue):
    return {
        'assignee': parse_named_user(issue.assignee),
        'assignees': [parse_named_user(assignee) for assignee in issue.assignees],
        'body': issue.body,
        'closed_at': issue.closed_at,
        'closed_by': parse_named_user(issue.closed_by),
        'created_at': issue.created_at,
        'id': issue.id,
        'number': issue.number,
        'state': issue.state,
        'title': issue.title,
        'updated_at': issue.updated_at,
        'user': parse_named_user(issue.user),
        'html_url': issue.html_url,
        'url': issue.url
    }

def parse_comment(comment):
    return {
        'body': comment.body,
        'id': comment.id,
        'updated_at': comment.updated_at,
        'created_at': comment.created_at,
        'html_url': comment.html_url,
        'user': parse_named_user(comment.user)
    }
    
def parse_review_comment(review_comment):
    return {
        'body':review_comment.body,
        'commit_id':review_comment.commit_id,
        'created_at': review_comment.created_at,
        'diff_hunk':review_comment.diff_hunk,
        'id':review_comment.id,
        'in_reply_to_id':review_comment.in_reply_to_id,
        'original_commit_id':review_comment.original_commit_id,
        'original_position':review_comment.original_position,
        'path':review_comment.path,
        'position':review_comment.position,
        'user':parse_named_user(review_comment.user),
        'url': review_comment.url
    }
    
def parse_commit(commit):
    return {
        'author': parse_named_user(commit.author),
        'message': commit.commit.message,
        'commit_html_url': commit.commit.html_url,
        'commit_sha': commit.commit.sha,
        'committer': parse_named_user(commit.committer),
        'files': [parse_file(file) for file in commit.files],
        'html_url': commit.html_url,
        'parents': [pcommit.sha for pcommit in commit.parents],
        'sha': commit.sha,
        'additions': commit.stats.additions,
        'deletions': commit.stats.deletions,
        'total': commit.stats.total,
        'statuses': [parse_status(status) for status in commit.get_statuses()],
        'url': commit.url
    }
   
def parse_status(commit_status):
    return {
        'created_at': commit_status.created_at,
        'creator': parse_named_user(commit_status.creator),
        'description': commit_status.description,
        'id': commit_status.id,
        'state': commit_status.state,
        'context': commit_status.context,
        'target_url': commit_status.target_url,
        'url': commit_status.url
    }
    
def parse_file(file):
    return {
         'additions':file.additions,
         'changes':file.changes,
         'contents_url': file.contents_url,
         'deletions': file.deletions,
         'filename': file.filename,
         'patch': file.patch,
         'previous_filename': file.previous_filename,
         'raw_url': file.raw_url,
         'sha': file.sha,
         'status':file.status
    }
    
#%%
   
def process_pull_request(pull, split_slug, g, token_queue):
    pull_dict = parse_pull_request(pull)
                    
    pull_dict["project_name"] = split_slug[1]
    pull_dict["project_owner"] = split_slug[0]
    
    pull_dict["raw_comments"] = []
    
    check_header_and_refresh(g, token_queue)
    
    pull_dict["commits"] = []
    
    commits = pull.get_commits()
    
    did_commits = 0
    
    for commit in commits:
        parsed_commit = parse_commit(commit)
        
        parsed_commit["project_name"] = split_slug[1]
        parsed_commit["project_owner"] = split_slug[0]
        
        pull_dict["commits"].append(parsed_commit)
        
        did_commits += 1
        
        if did_commits == 10:
            did_commits = 0
            check_header_and_refresh(g, token_queue)
    
    check_header_and_refresh(g, token_queue)
    
    gh_comments = pull.get_issue_comments()
    
    did_comments = 0
    
    for comment in gh_comments:
        pull_dict["raw_comments"].append(parse_comment(comment))
        
        did_comments += 1
        
        if did_comments == 25:
            check_header_and_refresh(g, token_queue)
            did_comments = 0
        
    pull_dict["review_comments"] = []
    
    gh_review_comments = pull.get_review_comments()
    
    did_comments = 0
    
    for review_comment in gh_review_comments:
        pull_dict["review_comments"].append(parse_review_comment(review_comment))
        
        did_comments += 1
        
        if did_comments == 30:
            check_header_and_refresh(g, token_queue)
            did_comments = 0
            
    return pull_dict;

#%%
def process_project(project):   

    token_queue = gh_tokens.gh_tokens
    
    new_token = token_queue.get()
    
    token_queue.put(new_token)
    
    g = Github(new_token, per_page=100)
    
    fail_count = 0   

    travis_api_headers = {'Travis-API-Version' : '3', 'Authorization' : 'token {}'.format(travis_token.travis_token)}
    
    #This returns the first build for that slug as recorded by travis. 
    travis_url_base = "https://api.travis-ci.org/repo/{}/builds?sort_by=finished_at&limit=1"
    
    allowed_failures = 5
    
    project_dal = ProjectDal()
    issue_dal = IssueDal()
    pull_request_dal = PullRequestDal()
    commit_dal = CommitDal()
        
    while True:
        try:
            if project_dal.project_inserted(project["slug"]):
                print("Skipping {}".format(project["slug"]))
                break
                
            split_slug = project['slug'].split("/")
        
            first_build_age_url = travis_url_base.format(urllib.parse.quote_plus(project["slug"]))

            first_build_age_response = requests.get(first_build_age_url, headers = travis_api_headers)

            if first_build_age_response.status_code not in [200, 403, 404]:
                print("Could not access data from travis")

                time.sleep(2)

                first_build_age_response = requests.get(first_build_age_url, headers = travis_api_headers)

                if first_build_age_response.status_code not in [200, 403, 404]:
                    print(first_build_age_url)
                    print("Travis servers failed twice on above url")
                    break

            first_build_age_dict = first_build_age_response.json()

            if first_build_age_dict['@type'] == 'error' or len(first_build_age_dict['builds']) == 0 or first_build_age_dict['builds'][0]['started_at'] is None:
                print("No builds or projects found for {}".format(project['slug']))
                project_dal.insert_project({"full_name": project["slug"], "succeeded": False})
                break    
                
            first_build_date = datetime.datetime.strptime(first_build_age_dict['builds'][0]['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                            
            check_header_and_refresh(g, token_queue)
            
            repo = g.get_repo(project["slug"])
            
            repo_dict = parse_repo(repo)
            
            repo_dict["first_build_date_travis"] = first_build_date
            
            check_header_and_refresh(g, token_queue)
            
            pulls = repo.get_pulls(state='closed')
            
            repo_dict["pull_requests"] = []
                            
            did_pulls = 0
            completed_pulls = 0
            
            for pull in pulls:
                
                pull_fail_count = 0;
                
                pull_dict = {}
                
                while pull_fail_count < 3:
                    try:
                        pull_dict = process_pull_request(pull, split_slug, g, token_queue)
                        break;
                    except:
                        pull_fail_count += 1
                        print("Failed scraping pull request #{}".format(completed_pulls))
                        
                repo_dict["pull_requests"].append(pull_dict)
                    
                did_pulls += 1
                completed_pulls += 1
                
                if completed_pulls % 500 == 0:
                    print("Did {} pull requests".format(completed_pulls))
                
                if did_pulls == 30:
                    check_header_and_refresh(g, token_queue)
                    did_pulls = 0
                    
            issues = repo.get_issues(state='closed')
            
            repo_dict["issues"] = []
            
            did_issues = 0
            completed_issues = 0
            
            for issue in issues:
                
                if not isinstance(issue.pull_request, github.IssuePullRequest.IssuePullRequest):
                
                    issue_dict = parse_issue(issue)

                    check_header_and_refresh(g, token_queue)

                    gh_comments = issue.get_comments()

                    issue_dict["raw_comments"] = []
                    
                    issue_dict["project_name"] = split_slug[1]
                    issue_dict["project_owner"] = split_slug[0]

                    did_comments = 0

                    for comment in gh_comments:
                        issue_dict["raw_comments"].append(parse_comment(comment))

                        did_comments += 1

                        if did_comments == 30:
                            check_header_and_refresh(g, token_queue)
                            did_comments = 0
                    
                    completed_issues += 1
                    
                    if completed_issues % 500 == 0:
                        print("Did {} issues".format(completed_issues))
                        
                    repo_dict["issues"].append(issue_dict)
                    
                did_issues += 1
                
                if did_issues == 30:
                    check_header_and_refresh(g, token_queue)
                    did_issues = 0
                                          
            issue_dal.insert_issues(repo_dict["issues"])
            repo_dict.pop("issues", None)
            
            # Ensure that we save commits to their own collection
            # then replace the commit objects with an array of sha hashes
            for pr in repo_dict["pull_requests"]:
                commit_dal.insert_commits(pr["commits"])
                pr["commits"] = [commit["sha"] for commit in pr["commits"]]
            
            pull_request_dal.insert_pull_requests(repo_dict["pull_requests"])
            repo_dict.pop("pull_requests", None)
            
            repo_dict["succeeded"] = True
            
            project_dal.insert_project(repo_dict)   
            
            #If this project has been scraped break from the While True
            #to start processing the next project.
            break

        except Exception as e:
            print("Failed {} with {}".format(project["slug"], e))
            print(traceback.format_exc())
            fail_count += 1
            
            if fail_count >= allowed_failures:
                project_dal.insert_project({"full_name": project["slug"], "succeeded": False})
                print("Skipped {} because of the too high failure count".format(project["slug"]))
                break
    
    
#%%
    
from github import Github
from math import ceil
from bson import json_util
from project_dal import ProjectDal
from issue_dal import IssueDal
from pull_request_dal import PullRequestDal
from commit_dal import CommitDal

import urllib.parse
import requests
import datetime
import json
import time
import os
import datetime
import gh_tokens
import travis_token
import traceback

import multiprocessing

with multiprocessing.Pool(4) as p:
    p.map(process_project, found_projects)

        
            
            
#%%
