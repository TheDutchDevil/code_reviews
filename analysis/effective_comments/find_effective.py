# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:22:54 2018

@author: natha
"""

import re

line_number_hunk_regex_raw = "((^|\\n)\@\@\ -(\d+(|,\d+))\ \+(\d+(|,\d+))\ \@\@)"

line_number_hunk_regex = re.compile(line_number_hunk_regex_raw)

'''
Given an item first checks whether it is a comment or 
commit. Then return the correct date field for the item. 
'''
def return_date_for_pr_or_commit(item):
    if "sha" in item:
        return item["date"]
    elif "original_commit_id" in item:
        return item["created_at"]
    else:
        raise ValueError("Ehm, this is not a code comment or commit")
        
'''
Method which given a file (and the patch which is part of that file) and 
placed comments updates all comments in that file with their new position
based on the diff of the file. 

For example, if 20 lines are added to the start of the file, and there is 
a comment at line 300, then the location of the comment is updated to be
at line 320. This to account for the lines that have been added.

Additionally, this method counts the effective comments that have 
been found so far. And in turn, returns all of the effective comments
that have been found. While removing them from the placed_comments 
set.
'''
def update_placed_comments_for_file(file, placed_comments):

    found_comments = 0

    for file_comment in list([rc for 
                        rc in placed_comments 
                        if rc["path"] == file["filename"] and "eff_track_line" in rc]):
        patch = file["patch"]
        
        if patch is None:
            # This is a serious error condition! Meaning this file can not be processed
            return found_comments
        
        curr_pos_in_old = 0
        curr_pos_in_new = 0
        
        # Update this to reflect the running delta of all hunks in this file
        lines_delta = 0

        updated_position = False
        
        for line in patch.split("\n"):
            if line.startswith("@@"):
                hunk_header_match = line_number_hunk_regex.match(line)

                curr_pos_in_old = int(hunk_header_match.group(3).split(",")[0])

                curr_pos_in_new = int(hunk_header_match.group(5).split(",")[0])
                
                # Positive for added lines
                # negative for removed lines
                lines_delta = curr_pos_in_new - curr_pos_in_old
                
                # At this point the diff passed the location of the comment. 
                # We update the old position with the new position in the
                # file so far (we do not care about a delta below the comment) and
                # we're done
                if curr_pos_in_old > file_comment["eff_track_line"]:
                    file_comment["eff_track_line"] += lines_delta
                    updated_position = True
                    break

            elif line.startswith("-"):
                curr_pos_in_old += 1
            elif line.startswith("+"):
                curr_pos_in_new += 1
            elif line.startswith(" "):
                curr_pos_in_old += 1
                curr_pos_in_new += 1
            elif line.startswith("\\"):
                pass                                                 
            else:
                print(line)
                raise ValueError("Horror, there is diff panic")

            if file_comment["eff_track_line"] == curr_pos_in_old:
                placed_comments.remove(file_comment)
                found_comments += 1
                updated_position = True
                break

        if not updated_position:
            # Calculate the new lines delta and update the position

            lines_delta = curr_pos_in_new - curr_pos_in_old
            file_comment["eff_track_line"] += lines_delta

    return found_comments

'''
We do a sort of sweep line algorithm, where we sort commits and line 
comments on the time they have been posted. We go through them both 
chronologically, for a code comment we note its position, for a commit
we extract the position of the diff(s) and we note whether they 
intersect with any of the existing comments. If they intersect, we 
mark the comment as having been change inducing. 

Furthermore, we update the position of existing comments to account
for the lines that have been added or removed in diffs. 
'''
def process_pr(pr):
    
    num_effective_comments = 0
    
    comments = sorted([rc for rc in pr["review_comments"] if rc["in_reply_to_id"] is None], key=lambda comment : comment["created_at"])
    commits = list([commit for commit in pr["commits"] if "date" in commit])
    
    commits = list([cmt for cmt in commits if cmt is not None])
       
    commits.sort(key = lambda commit : commit["date"])
    
    if len(comments) == 0:
        return 0
        
    if len(commits)  == 0:
        print("\tOh misery! PR with number {} has no dated commits".format(pr["number"]))
        return 0
        
    merged_list = commits + comments
    
    merged_list.sort(key = return_date_for_pr_or_commit)
    
    placed_line_comments = []
    
    made_commits = {}
    
    for item in merged_list:
        # Only process newly placed comments, don't bother with comments
        # that are placed as a reaction
        if "original_commit_id" in item:
            # Add the comment on the moment it has been placed and
            # attribute it with the closest location in the new part of the 
            # diff
            placed_line_comments.append(item)

            lines = item["diff_hunk"].split("\n")
            
            curr_pos_in_old = 0
            curr_pos_in_new = 0
            
            lines_done = 0
            
            for line in lines:                
                # The below bit updates the lines based on the counter
                if line.startswith("@@"):
                    hunk_header_match = line_number_hunk_regex.match(line)
                    
                    curr_pos_in_old = int(hunk_header_match.group(3).split(",")[0])
                                        
                    curr_pos_in_new = int(hunk_header_match.group(5).split(",")[0])
                    
                elif line.startswith("-"):
                    curr_pos_in_old += 1
                elif line.startswith("+"):
                    curr_pos_in_new += 1
                elif line.startswith(" "):
                    curr_pos_in_old += 1
                    curr_pos_in_new += 1
                elif line.startswith("\\"):
                    pass
                else:
                    print(line)
                    raise ValueError("Horror, there is diff panic")
                    
                lines_done += 1
                
                if item["original_position"] == lines_done:
                    # This is where the comment is --> record
                    # the position in the new file as the location 
                    # of this comment. 
                    #
                    # That way we can compare later commits to see
                    # if they came close to this comment
                    
                    item["eff_track_line"] = curr_pos_in_new
        
            
        elif "sha" in item:
            
            made_commits[item["sha"]] = item
            
            for file in item["files"]:
                # If the file has been modified we need to do two things.
                # Check if any omments were near any of the lines that have
                # been changed in this commit.
                # and if lines have been added or removed we need to update
                # the location of currently placed comments to reflect the
                # fact that they have changed by position by this commit
                if file["status"] == 'modified':
                    num_effective_comments += update_placed_comments_for_file(file, placed_line_comments)
                    
                                
                # If the file has been renamed we should update all comments in the old file to
                # the name of the new file, afterwards we should still run the file through the 
                # comment checker, as it might be the case that a patch is included in the 
                # rename action. If the file has been modified and renamed at the same time.
                elif file["status"] == "renamed":
                    for comment in [pc for pc in placed_line_comments if pc["path"] == file["previous_filename"]]:
                        comment["path"] = file["filename"]
                    
                    num_effective_comments += update_placed_comments_for_file(file, placed_line_comments)

                # If the file is deleted any comments in the 
                # file have induced some form of change
                elif file["status"] == "removed":
                    for file_comment in [rc for rc in placed_line_comments if rc["path"] == file["filename"]]:
                        num_effective_comments += 1
                        placed_line_comments.remove(file_comment)
                    
        else:
            raise ValueError("Ehm this is not a code comment or commit")
    return num_effective_comments
    

