from sklearn.metrics import cohen_kappa_score

rater_left = []
rater_right = []

with open('100-sample-rating-2-raters.csv') as fp:
    lines = fp.readlines()

    for line in lines[1:]:
        rater_left.append(line.split(",")[0])
        rater_right.append(line.split(",")[1].replace("\n", ""))

print(cohen_kappa_score(rater_left, rater_right))