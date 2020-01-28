# Introduction

This repository contains the code and data for the SANER 2020 paper 
_The Silent Helper: The Impact of Continuous Integration on Code Reviews_ ([PDF](https://cassee.dev/files/CI-silent.pdf)). Joint work between
[Nathan Cassee](https://cassee.dev) (TU/e), [Bogdan Vasilescu](https://bvasiles.github.io/) (CMU), 
and [Alexander Serebrenik](https://www.win.tue.nl/~aserebre/) (TU/e). 

There are several parts to this repository, data collection and pre-processing has been done using
Python, some analysis and the plots have been generated using Python Jupyter Notebooks, and 
the statistical models have been run using Jupyter Notebooks in R. 

# Steps

For each of the steps this readme will direct you to some files of note. 

## Scraping

The main file used to scrape information the Python script
`scrape_project_from_github.py`. As input this file requires
a .csv containing the slugs of the repositories that should be 
mined, and a connection to a running [GHTorrent](http://ghtorrent.org/) 
instance. As output this script requires connection to a MongoDB
instance, such that scraped items can be stored. 

For each slug in the input csv the script first queries the `GHTorrent`
to determine whether that project has more than 1,000 general 
pull-request comments, and after doing this for all projects
saves the intermediate results to a `.json` file.

For each `GitHub` project with more than 1,000 general comments
the scrape loop is executed.

### Scrape loop

We first check whether the project has at least one Travis build,
using the Travis API (This requires a Travis API key to be present in
`travis_token.py`). If the project has a Travis build
we continue scraping, and using 
[PyGitHub](https://pygithub.readthedocs.io/en/latest/introduction.html)
we scrape all closed pull-requests, associated comments, review comments
and commits, and all closed issues for that project. **Note:** direct commits
only pushed to the repository are **not** scraped. 

The resulting data is then inserted in a MongoDB instance. Where project
data is split over 4 collections because of MongoDB limitations. These
4 collections are, `projects`, `issues`, `pull_requests`, and `commits`.

To efficiently scrape data from `GitHub` the scrape script uses several
threads, and cycles through a set of tokens defined in `gh_tokens.py`
(More tokens == more speed).

## Processing

When it comes to processing the scraped data there are several Python
scripts and cells that take data in the MongoDb instance and augment it
by adding fields. 

* `analysis/first_travis_build.ipynb`:<br><br>
This notebook contains a set of cells that uses a set 
of heuristics (including the GitHub 
[commit statuses](https://developer.github.com/v3/repos/statuses/)) to
find the oldest Travis build associated with a pull-request, and to determine
whether Travis was the first CI service used by the project. This result is then
written to the MongoDB database by setting the fields `status_travis_date (date)`
and `travis_is_oldest_ci (bool)`. 

* `find_effective_comments.py`: <br><br>
This Python script uses the script `analysis/effective_comments/find_effective.py`
to process all pull requests in the MongoDB instance to find effective
review comments as defined by 
[Bosu et al.](https://www.microsoft.com/en-us/research/publication/characteristics-of-useful-code-reviews-an-empirical-study-at-microsoft/).
This information is needed to run the RDD model that models the impact
of Continuous Integration on effective comments in code reviews. 




## Analysis

## Models

# Cite

Please use the following BibTex snippet to cite this work:

```
@misc{}
```
