import MySQLdb
db = MySQLdb.connect(passwd="ghtorrent_restore",db="ghtorrent_06_19",user="ghtorrent")

c = db.cursor()

c.execute("Select max(projects.id), min(projects.id) from projects where total_number_pr_comments = 0")

counts = c.fetchone()

min_proj = counts[1]
max_proj = counts[0]

for i in range(min_proj, max_proj + 1):
    c.execute("""update projects
                    set projects.total_number_pr_comments = ( select count(projects.id)
                        from 
                        pull_requests pr, 
                        issues iss, 
                        issue_comments iss_cms
                        where 
                            projects.id = pr.base_repo_id and
                            pr.id = iss.pull_request_id and
                            iss.pull_request = true and
                            iss_cms.issue_id = iss.id         
                            group by projects.id ), 
                    projects.total_number_prs = ( select count(projects.id)
                            from 
                            pull_requests pr
                            where projects.id = pr.base_repo_id      
                            group by projects.id )
                        where projects.id = {} and total_number_pr_comments = 0
        """.format(i))
