# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 11:16:31 2018

@author: natha
"""

import random
import datetime

import matplotlib.pyplot as plt
import seaborn as sn
import numpy as np

def split_prs_on_build_date(project, prs, equal_number = False, field_name="status_travis_date"):
    
    if field_name not in project.keys():
        raise ValueError("No status date in project")
    
    prs_before = [pr for pr in prs if pr["created_at"] < (project[field_name] - datetime.timedelta(days=15))]
    prs_after = [pr for pr in prs if pr["created_at"] > (project[field_name] + datetime.timedelta(days=15))]
    
    if equal_number:
        if len(prs_before) > len(prs_after):
            indices = random.sample(range(len(prs_before)), len(prs_after))
            
            prs_before = [prs_before[i] for i in indices]
        elif len(prs_before) < len(prs_after):
            indices = random.sample(range(len(prs_after)), len(prs_before))
            
            prs_after = [prs_after[i] for i in indices]
    
    return (prs_before, prs_after)

def do_before_after_boxplot(before_data, after_data, names, title, ylabel, yscale="log"):
    plt.figure(figsize=(15,5))


    def set_box_color(bp, color):
        plt.setp(bp['boxes'], color=color)
        plt.setp(bp['whiskers'], color=color)
        plt.setp(bp['caps'], color=color)
        plt.setp(bp['medians'], color=color)   

    bpl = plt.boxplot(before_data, positions=np.array(range(len(before_data)))*2.0-0.4, sym='o', widths=0.6)
    bpr = plt.boxplot(after_data, positions=np.array(range(len(after_data)))*2.0+0.4, sym='o', widths=0.6)
    set_box_color(bpl, '#D7191C') # colors are from http://colorbrewer2.org/
    set_box_color(bpr, '#2C7BB6')

    # draw temporary red and blue lines and use them to create a legend
    plt.plot([], c='#D7191C', label='Before CI')
    plt.plot([], c='#2C7BB6', label='After CI')
    plt.legend()

    plt.xticks(range(0, len(names) * 2, 2), names, rotation="vertical")
    plt.xlim(-2, len(names)*2)

    plt.yscale(yscale)

    plt.title(title)
    plt.ylabel(ylabel)

    plt.show()