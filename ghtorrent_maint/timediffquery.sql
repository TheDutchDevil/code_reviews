select pr.id as gh_id, pr.name as slug, TIMESTAMPDIFF(MONTH, min(iss.created_at), max(iss.created_at)) as timediff, count(iss.id) as prs from projects pr, issues iss
where iss.pull_request = 1 and iss.repo_id = pr.id
group by pr.id
having TIMESTAMPDIFF(MONTH, min(iss.created_at), max(iss.created_at)) > 24 and count(iss.id) > 24;