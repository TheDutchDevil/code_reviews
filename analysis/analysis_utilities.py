# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 11:16:31 2018

@author: natha
"""

import random
import datetime

def split_prs_on_build_date(project, prs, equal_number = False):
    
    if "status_travis_date" not in project.keys():
        raise ValueError("No status date in project")
    
    prs_before = [pr for pr in prs if pr["created_at"] < (project["status_travis_date"] - datetime.timedelta(days=15))]
    prs_after = [pr for pr in prs if pr["created_at"] > (project["status_travis_date"] + datetime.timedelta(days=15))]
    
    if equal_number:
        if len(prs_before) > len(prs_after):
            indices = random.sample(range(len(prs_before)), len(prs_after))
            
            prs_before = [prs_before[i] for i in indices]
        elif len(prs_before) < len(prs_after):
            indices = random.sample(range(len(prs_after)), len(prs_before))
            
            prs_after = [prs_after[i] for i in indices]
    
    return (prs_before, prs_after)