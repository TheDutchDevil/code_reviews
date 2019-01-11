import code_reviews.analysis.effective_comments.find_effective as find_effective

import datetime
import pytest

class TestReturnDateForCommentOrCommit():

    def test_correct_date_returned_for_comment(self):
        date = datetime.datetime.now()

        item = {'original_commit_id' : '432fda', 'created_at': date}

        received_date = find_effective.return_date_for_pr_or_commit(item)

        assert date == received_date

    def test_correct_date_returned_for_commit(self):
        date = datetime.datetime.now()

        item = {'sha' : '432fda', 'date': date}

        received_date = find_effective.return_date_for_pr_or_commit(item)

        assert date == received_date

    def test_error_raised_for_missing_key(self):
        date = datetime.datetime.now()

        item = { 'date': date}

        with pytest.raises(ValueError):
            find_effective.return_date_for_pr_or_commit(item)

        
