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
def review_comment_object(created_at_offset, original_position, path = "a/something.py"):
    return {
        'in_reply_to_id': None,
        'created_at': base_date + created_at_offset,
        'original_commit_id': 'fdasfdjakl234',
        'original_position': original_position,
        'path': path
    }

def pull_request_object(comments = [], commits = [], number = 342):
    return {
        'number': number,
        'review_comments': comments,
        'commits': commits
    }

def commit_object(created_at_offset):
    return {
        'date': base_date + created_at_offset
    }

'''
Given 5 pieces of information creates a hunk of x modified lines, with the right
@@ header. 
'''
def create_hunk(start_old, length_old, start_new, length_new, modified_lines):
    header_line = "@@ -{},{} +{},{} @@".format(start_old, length_old,
                                                    start_new, length_new)
    
    # This is the padding above and below the diff.
    unchanged_lines = min(length_new, length_old) - modified_lines

    unchanged_top = unchanged_lines // 2
    unchanged_bottom = unchanged_lines // 2 + unchanged_lines % 2

    lines = [header_line]

    lines += [" fdsklajf sdaf " for i in range(unchanged_top)]
    
    if length_old > length_new:
        # Lines have been removed
        lines += ["-jfkdlajfkl dajsfkl " for i in range(abs(length_old - length_new))]
    elif length_old < length_new:
        # Lines have been added
        lines += ["+jfkdlajfkl dajsfkl " for i in range(abs(length_old - length_new))]

    lines += ["-jfkl djaskl fjdas" for i in range(modified_lines)]
    lines += ["+ fjklasdj fklasdjk f" for i in range(modified_lines)]

    lines += [" fjdklasjfklasd  " for i in range(unchanged_bottom)]

    return '\n'.join(lines)

