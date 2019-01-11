import code_reviews.analysis.effective_comments.find_effective as find_effective

import datetime
import pytest

from dateutil.relativedelta import relativedelta

'''
Base date used as a starting point for all commits and comments, used
for constructing the test objects.

Base date is a year behind the current date.
'''
base_date = datetime.datetime.now() - relativedelta(years= 1)

class TestFindEffectiveProcessPr():

    def test_zero_returned_for_no_comments(self):
        pr = pull_request_object()

        assert find_effective.process_pr(pr) == 0


    def test_zero_returned_for_no_commits(self):
        pr = pull_request_object(comments=[
            review_comment_object(relativedelta(days=1), 10)
        ])

        assert find_effective.process_pr(pr) == 0

    def test_zero_returned_for_pr_with_one_commit_and_one_comment(self):
        pass


'''
Helper method that returns a review comment object suited for the 
process_pr method. 
'''
def review_comment_object(created_at_offset, original_position):
    return {
        'in_reply_to_id': None,
        'created_at': base_date + created_at_offset,
        'original_commit_id': 'fdasfdjakl234',
        'original_position': original_position
    }

def pull_request_object(comments = [], commits = [], number = 342):
    return {
        'number': number,
        'review_comments': comments,
        'commits': commits
    }