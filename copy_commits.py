# -*- coding: utf-8 -*-
"""

This file copies all commits from myisam to the innodb storage engine. 
Hopefully this increases the query performance of the search queries. 

Created on Fri Nov 30 12:44:39 2018

@author: natha
"""

BATCH_SIZE= 20000

import MySQLdb

import math
from timeit import default_timer as timer

db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_restore",user="ghtorrent")

c = db.cursor()


c.execute("select max(id) from commits")

total_commits = c.fetchone()[0]

print("Total commits to do is {}".format(total_commits))

c.execute("select max(id) from commits_v2")

done_commits = c.fetchone()[0]

if done_commits is None:
    done_commits = 0

todo_commits = total_commits - done_commits

batches = math.ceil(todo_commits / BATCH_SIZE)

print("Already did {}, this leaves {} commits".format(done_commits, todo_commits))

print("This results in {} batches of {} commits".format(batches, BATCH_SIZE))

did_all_commits = False

did_batches = 0

lower = done_commits
higher = lower + BATCH_SIZE

while not did_all_commits:
        
    c_cursor = db.cursor()
    try:
        
        start = timer()
        
        c_cursor.execute("""insert into commits_v2 select * from commits c
                            where c.id > {} and c.id <= {}
                         """.format(lower, higher))
        
        c_cursor.close()
        
        db.commit()
        
        stop = timer()
        
        did_batches += 1
        lower += BATCH_SIZE
        higher += BATCH_SIZE
        
        print("Inserted {} commits in {} seconds, {} batches left".format(
                BATCH_SIZE, stop - start, batches - did_batches))
        
        if did_batches == batches:
            did_all_commits = True
    except:
        raise
    finally:
        db.rollback()