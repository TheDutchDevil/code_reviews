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
        pr = pull_request_object(comments=[
            review_comment_object(relativedelta(days=5), 12)
        ],
        commits=[
            commit_object(relativedelta(days=4))
        ])

        assert find_effective.process_pr(pr) == 0

    def test_one_returned_for_pr_with_two_commits_in_same_area(self):
        
        pr = pull_request_object(comments=[
            review_comment_object(relativedelta(days=5), 12)
        ],
        commits=[
            commit_object(relativedelta(days=4)),
            commit_object(relativedelta(days=7))
        ])        

        assert find_effective.process_pr(pr) == 1

    def test_no_effective_comments_for_two_different_files(self):
        pr = pull_request_object(comments=[
            review_comment_object(relativedelta(days=5), 12)
        ],
        commits=[
            commit_object(relativedelta(days=4)),
            commit_object(relativedelta(days=7), files =[
                file_object(filename="b/something.py")
            ])
        ])        

        assert find_effective.process_pr(pr) == 0

    def test_effective_comment_found_after_removing_lines(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 8, hunks=[
                    hunk(100,116,100,116, modified_lines = 6)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,60,10,20)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(55,15,55,15,modified_lines=5)])
                ])
            ]
        )

        assert find_effective.process_pr(pr) == 1

    def test_effective_comment_found_after_adding_lines(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 8, hunks=[
                    hunk(100,116,100,116, modified_lines = 6)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,20,10,60)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(140,15,140,15,modified_lines=5)])
                ])
            ]
        )

        assert find_effective.process_pr(pr) == 1

    def test_no_comment_found_after_adding_lines(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 8, hunks=[
                    hunk(100,116,100,116, modified_lines = 6)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,20,10,60)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(70,15,70,15,modified_lines=5)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 0

    def test_comment_found_after_adding_lines_behind_comment_1(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(50,10,50,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(70,20,70,60)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(50,10,50,10,modified_lines=5)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 1

    def test_comment_found_after_adding_lines_behind_comment_2(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(50,10,50,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,20), 
                            hunk(90,20,100,60)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(60,10,60,10,modified_lines=5)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 1

    def test_comment_found_after_file_rename(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(50,10,50,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,20), 
                            hunk(90,20,100,60)])
                ]),
                commit_object(relativedelta(days=8), files= [
                    file_object(hunks=[hunk(60,10,60,10,modified_lines=5)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 1

    def test_comment_found_after_many_inserts(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(300,10,300,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,20), 
                            hunk(200,20,210,80),
                            hunk(302, 20, 372, 20, modified_lines=10)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 1

    def test_no_comment_found_after_many_inserts(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(370,10,370,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,20), 
                            hunk(200,20,210,80),
                            hunk(302, 20, 372, 20, modified_lines=10)])
                ])
            ]
        )
        assert find_effective.process_pr(pr) == 0


'''
Given 5 pieces of information creates a hunk of x modified lines, with the right
@@ header. 
'''
def hunk(start_old, length_old, start_new, length_new, modified_lines = 0):
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

def file_object(filename = "a/something.py", file_status = 'modified',
            hunks = [hunk(10, 15, 10, 15, modified_lines = 5)]):
    return {
        'filename': filename,
        'status': file_status,
        'patch': "\n".join(hunks)
    }

    

def commit_object(created_at_offset, files = [file_object()]):
    return {
        'date': base_date + created_at_offset,
        'files': files,
        'sha': 'fdjakl fdafj das f32r'
    }

'''
Helper method that returns a review comment object suited for the 
process_pr method. 
'''
def review_comment_object(created_at_offset, original_position, path = "a/something.py",
                        hunks = [hunk(10,15,10,15, modified_lines = 5)]):
    return {
        'in_reply_to_id': None,
        'created_at': base_date + created_at_offset,
        'original_commit_id': 'fdasfdjakl234',
        'original_position': original_position,
        'path': path,
        'diff_hunk': "\n".join(hunks)
    }

def pull_request_object(comments = [], commits = [], number = 342):
    return {
        'number': number,
        'review_comments': comments,
        'commits': commits
    }

