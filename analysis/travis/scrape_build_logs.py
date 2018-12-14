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
                