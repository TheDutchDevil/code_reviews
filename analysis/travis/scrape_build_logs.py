# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 17:58:45 2018

Script that scrapes the Travis API to collect build logs for a build identifier

@author: natha
"""

import time
import requests


import travis.travis_token as tt

TRAVIS_TOKEN = tt.travis_token

BASE_TRAVIS_URL = "https://api.travis-ci.org"

TRAVIS_HEADER = {'Travis-API-Version' : '3', 
                 'Authorization' : 'token {}'.
                         format(TRAVIS_TOKEN)}


def retrieve_build_for_identifier(build_identifier):
    builds_url = "{}/{}/{}".format(BASE_TRAVIS_URL, 'build', build_identifier)
    
    build_response = requests.get(builds_url, headers = TRAVIS_HEADER)
    
    if build_response.status_code not in [200, 403, 404]:
        print("Could not access data from travis")
    
        time.sleep(2)
    
        build_response = requests.get(builds_url, headers = TRAVIS_HEADER)
    
        if build_response.status_code not in [200, 403, 404]:
            raise ValueError("Could not scrape a build from Travis")
    
    build_data = build_response.json()
    
    if build_data['@type'] == 'error':
        raise ValueError("Could not scrape build from Travis response was {}"
                         .format(build_data))
        
    return build_data

def extract_job_ids_for_build(build_data):
    if len(build_data["jobs"]) == 0:
        raise ValueError("No jobs for this build")
    
    job_ids = []
    
    for job in build_data["jobs"]:
        job_ids.append(job["id"])
        
    return job_ids
        

def retrieve_build_log_for_job_id(job_identifier):
    build_log_url = "{}/{}/{}/log".format(BASE_TRAVIS_URL, "job", job_identifier)
    
    actual_headers = dict(TRAVIS_HEADER)
    
    # This is needed so that the build log is not in some weird decoded unreadable
    # format
    actual_headers["Accept"] = "text/plain"
    
    log_response = requests.get(build_log_url, headers = actual_headers)
    
    if log_response.status_code not in [200]:
        print("Could not retrieve build log from Travis, status code is {}".
              format(log_response.status_code))
        
    return log_response.text

def retrieve_build_identifier_from_travis_url(url):
    if "travis-ci.org" not in url:
        raise ValueError("The url {} is not a valid travis url"
                        .format(url))
        
    identifier = url.split("builds/")[1].split("/")[0]
    
    return identifier

'''
Given a set of build identifiers, goes to Travis to collects all 
assorted logs and returns these logs. As a travis build consists 
out of several jobs one build identifier might return more than 
one log.

Return type is an array of string, where each string is a complete
build log as recorded by Travis. 
'''
def build_logs_for_identifiers(identifiers):
    log_output = []
    
    for identifier in identifiers:
        build_data = retrieve_build_for_identifier(identifier)
        
        job_ids = extract_job_ids_for_build(build_data)
        
        for job_id in job_ids:
            log_output.append(retrieve_build_log_for_job_id(job_id))
            
    return log_output
            