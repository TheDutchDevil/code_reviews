# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 17:04:10 2018

@author: Nathan
"""

import multiprocessing
import threading
import time
import inspect
import os

dirname = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
filename = os.path.join(dirname, 'gh_tokens_list')


m = multiprocessing.Manager()

gh_tokens = m.Queue()

tokens_added = []

def read_tokens():
    print("Reading tokens")
    with open(filename) as fp:  
        for cnt, line in enumerate(fp):
            if line == "" or "," not in line:
                continue

            token = line.split(",")[0]
            comment = line.split(",")[1]

            if token not in tokens_added:
                tokens_added.append(token)
                gh_tokens.put(token)
                print("Added {}'s token".format(comment.replace("\n", "")))

    
    threading.Timer(10.0, read_tokens).start()

read_tokens()


