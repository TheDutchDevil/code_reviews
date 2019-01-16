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

    def test_file_rename_comment_found_1(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(370,10,370,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,10, modified_lines=4)],
                    file_status='renamed', previous_filename='a/something.py',
                    filename='b/something.py'),
                    file_object(hunks=[
                        hunk(370,10,370,10, modified_lines=4)
                    ], filename='b/something.py')
                ])
            ]
        )

        assert find_effective.process_pr(pr) == 1

    def test_file_rename_comment_found_2(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(370,10,370,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(370,10,370,10, modified_lines=4)],
                    file_status='renamed', previous_filename='a/something.py',
                    filename='b/something.py')
                ])
            ]
        )

        assert find_effective.process_pr(pr) == 1

    def test_file_renamed_no_comment_found(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(370,10,370,10, modified_lines = 4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,10, modified_lines=4)],
                    file_status='renamed', previous_filename='a/something.py',
                    filename='b/something.py'),
                    file_object(hunks=[
                        hunk(370,10,370,10, modified_lines=4)
                    ], filename='c/something.py')
                ])
            ]
        )

        assert find_effective.process_pr(pr) == 0

    def test_more_comments_after_unrelated_commits(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 5, hunks=[
                    hunk(100,10,100,10, modified_lines = 4)
                ]),
                review_comment_object(relativedelta(days=4), 5, 
                hunks=[hunk(200,10,200,10, modified_lines=4)])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(10,10,10,40, modified_lines=0)])
                ]),
                commit_object(relativedelta(days=5), files=[
                    file_object(hunks=[hunk(130,10,130,10, modified_lines=4)])
                ]),
                commit_object(relativedelta(days=7), files=[
                    file_object(hunks=[hunk(200,10,200,10, modified_lines=4)])
                ])
                
            ]
        )

        assert find_effective.process_pr(pr) == 2

    def test_two_hunks_in_comment_diff_no_effective_comment(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 18, hunks=[
                    hunk(100,10,100,10, modified_lines = 4),
                    hunk(200,10,200,10, modified_lines=4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(100,10,100,10, modified_lines=4)])
                ])
                
            ]
        )

        assert find_effective.process_pr(pr) == 0

    def test_two_hunks_in_comment_diff_effective_comment(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2), 18, hunks=[
                    hunk(100,10,100,10, modified_lines = 4),
                    hunk(200,10,200,10, modified_lines=4)
                ])
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=3), files=[
                    file_object(hunks=[hunk(200,10,200,10, modified_lines=4)])
                ])
                
            ]
        )

        assert find_effective.process_pr(pr) == 1

    '''
    Test case based on a false negative of PHP cake docs
    '''
    def test_php_cake_docs(self):
        pr = pull_request_object(
            comments=[
                review_comment_object(relativedelta(days=2, minutes=2), 6, hunks=[
                    "@@ -61,11 +61,11 @@ soit cachée. La valeur du temps peut être exprimé dans le format\n ``strtotime()``. (ex. \"1 hour\", ou \"3 minutes\").\n \n En utilisant l\'exemple d\'un controller d\'articles ArticlesController,\n-qui reçoit beaucoup de trafics qui ont besoins d\'être mise en cache:: \n+qui reçoit beaucoup de trafics qui ont besoins d\'être mise en cache::\n "
                ],path='fr/core-libraries/helpers/cache.rst')
            ],
            commits= [
                commit_object(relativedelta(days=1)),
                commit_object(relativedelta(days=2, minutes=4), files=[
                    file_object(hunks=[
                        "@@ -61,7 +61,7 @@ soit cachée. La valeur du temps peut être exprimé dans le format\n ``strtotime()``. (ex. \"1 hour\", ou \"3 minutes\").\n \n En utilisant l\'exemple d\'un controller d\'articles ArticlesController,\n-qui reçoit beaucoup de trafics qui ont besoins d\'être mise en cache::\n+qui reçoit beaucoup de trafic qui ont besoins d\'être mise en cache::\n \n     public $cacheAction = array(\n         \'view\' => 36000,"
                    ],
                    filename='fr/core-libraries/helpers/cache.rst')
                ])
                
            ]
        )

        

        assert find_effective.process_pr(pr) == 1

    def test_php_cake_docs_2(self):
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        mongo_client = MongoClient()

        database = mongo_client["graduation"]

        pull_requests_collection = database["pull_requests"]

        projects_collection = database["projects"]

        commits_collection = database["commits"]

        pr = pull_requests_collection.find_one({'number': 3077,'project_owner':'cakephp', 'project_name':'docs'})

        full_commits = list([commits_collection.find_one({'sha': commit_hash}) for commit_hash in pr["commits"]])

        print(len(full_commits))

        print(pr)

        print(full_commits[1])

        hashes = pr["commits"]

        print(full_commits[0]["date"])

        pr["commits"] = full_commits

        num_of_effective_comments = find_effective.process_pr(pr)

        print(num_of_effective_comments)



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
            hunks = [hunk(10, 15, 10, 15, modified_lines = 5)], 
            previous_filename = None):
    ret = {
        'filename': filename,
        'status': file_status,
        'patch': "\n".join(hunks)
    }

    if file_status == "renamed":
        ret['previous_filename'] = previous_filename

    return ret

    

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

