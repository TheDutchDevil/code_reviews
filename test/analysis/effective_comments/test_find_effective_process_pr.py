import code_reviews.analysis.effective_comments.find_effective as find_effective

import datetime
import pytest

class TestFindEffectiveProcessPr():

    def test_zero_returned_for_no_comments(self):
        pr = {
            'review_comments': [],
            'commits': []
        }

        assert find_effective.process_pr(pr) == 0


    def test_zero_returned_for_no_commits(self):
        pr = {
            'review_comments': [{'in_reply_to_id': None, 'created_at': datetime.datetime.now()}],
            'commits': [],
            'number': 32
        }

        assert find_effective.process_pr(pr) == 0