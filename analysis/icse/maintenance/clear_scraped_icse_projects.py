'''
This script is used to delete all projects from the mongodb instance that 
have the icse tag. This such that data collection can be reset
'''

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from dals.project_dal import ProjectDal


def verify():
    print("Are you sure you want to delete all scrape projects for icse? [y/n]")

    read = input()

    return read.lower() == "y"

if __name__ == "__main__":
    if verify():
        print("Deleting icse projects")

        projectDal = ProjectDal()

        projects = list(projectDal.find_projects({"scrape_type": "icse_1"}, {"full_name": 1}))

        print("Deleting {} icse projects".format(len(projects)))

        for project in projects:
            projectDal.delete_project(project["full_name"])

    else:
        print("Aborting")

