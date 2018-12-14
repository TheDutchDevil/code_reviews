# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 17:58:45 2018

Script that scrapes the Travis API to collect build logs for a build identifier

@author: natha
"""

import travis_token as tt

import time
import requests




TRAVIS_TOKEN = tt.travis_token

BASE_TRAVIS_URL = "https://api.travis-ci.org"

TRAVIS_HEADER = {'Travis-API-Version' : '3', 
                 'Authorization' : 'token {}'.
                         format(TRAVIS_TOKEN)}


def retrieve_build_for_identifier(build_identifier):
    builds_url = "{}/{}/{}".format(BASE_TRAVIS_URL, 'builds', build_identifier)
    
    build_response = requests.get(builds_url, headers = TRAVIS_HEADER)
    
    if build_response.status_code not in [200, 403, 404]:
        print("Could not access data from travis")
    
        time.sleep(2)
    
        build_response = requests.get(builds_url, headers = TRAVIS_HEADER)
    
        if build_response.status_code not in [200, 403, 404]:
            raise ValueError("Could not scrape a build from Travis")
    
    build_data = build_response.json()
    
    if build_data['@type'] == 'error':
        print(build_data)
        raise ValueError("Could not scrape build from Travis")
        
    
                