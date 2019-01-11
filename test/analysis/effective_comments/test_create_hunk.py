'''
Yes, even the test code has its own tests! this is to test the validity of the 
create hunk method
'''

from code_reviews.test.analysis.effective_comments.test_find_effective_process_pr import create_hunk

class TestCreateHunk():

    def test_header_included(self):
        hunk = create_hunk(10, 10, 10, 10, modified_lines = 0)

        first_line = hunk.split("\n")[0]

        assert first_line == "@@ -10,10 +10,10 @@"

    def test_unmodified_correct_length(self):        
        hunk = create_hunk(10, 10, 10, 10, modified_lines = 0)

        lines = hunk.split("\n")

        assert len(lines) == 11

    def test_unmodified_no_plus_or_minus(self):
        hunk = create_hunk(10, 10, 10, 10, modified_lines = 0)

        lines = hunk.split("\n")

        lines.pop(0)

        for line in lines:
            assert line[0] == " "

    def test_added_lines_hunk(self):
        hunk = create_hunk(10, 10, 10, 12, modified_lines = 0)

        header = hunk.split("\n")[0]

        assert header == "@@ -10,10 +10,12 @@"

    def test_added_lines_length(self):
        hunk = create_hunk(10, 10, 10, 12, modified_lines = 0)

        lines = hunk.split("\n")

        assert len(lines) == 13

    def test_added_lines_correct_sign(self):
        hunk = create_hunk(10, 10, 10, 12, modified_lines = 0)

        lines = hunk.split("\n")

        lines.pop(0)

        counted_none = 0
        counted_added = 0

        for line in lines:
            if line[0] == " ":
                counted_none += 1
            elif line[0] == "+":
                counted_added += 1
            assert line[0] == " " or line[0] == "+"

        assert counted_added == 2
        assert counted_none == 10

    def test_removed_lines_hunk(self):
        hunk = create_hunk(10, 13, 10, 10, modified_lines = 0)

        header = hunk.split("\n")[0]

        assert header == "@@ -10,13 +10,10 @@"

    def test_removed_lines_length(self):
        hunk = create_hunk(10, 13, 10, 10, modified_lines = 0)

        lines = hunk.split("\n")

        assert len(lines) == 14

    def test_removed_lines_correct_sign(self):
        hunk = create_hunk(10, 13, 10, 10, modified_lines = 0)

        lines = hunk.split("\n")

        lines.pop(0)

        counted_none = 0
        counted_removed = 0

        for line in lines:
            if line[0] == " ":
                counted_none += 1
            elif line[0] == "-":
                counted_removed += 1
            assert line[0] == " " or line[0] == "-"

        assert counted_removed == 3
        assert counted_none == 10

    def test_modified_lines_length(self):
        hunk = create_hunk(10, 15, 10, 15, modified_lines = 5)

        lines = hunk.split("\n")

        assert len(lines) == 21

    def test_modified_lines_correct_sign(self):
        hunk = create_hunk(10, 15, 10, 15, modified_lines = 5)
        lines = hunk.split("\n")

        lines.pop(0)

        counted_none = 0
        counted_removed = 0
        counted_added = 0

        for line in lines:
            if line[0] == " ":
                counted_none += 1
            elif line[0] == "-":
                counted_removed += 1
            elif line[0] == "+":
                counted_added += 1
            assert line[0] == " " or line[0] == "-" or line[0] == "+"

        assert counted_removed == 5
        assert counted_added == 5
        assert counted_none == 10

    def test_modified_and_added_lines_correct_sign(self):
        hunk = create_hunk(10, 15, 10, 20, modified_lines = 5)
        lines = hunk.split("\n")

        lines.pop(0)

        counted_none = 0
        counted_removed = 0
        counted_added = 0

        for line in lines:
            if line[0] == " ":
                counted_none += 1
            elif line[0] == "-":
                counted_removed += 1
            elif line[0] == "+":
                counted_added += 1
            assert line[0] == " " or line[0] == "-" or line[0] == "+"

        assert counted_removed == 5
        assert counted_added == 10
        assert counted_none == 10