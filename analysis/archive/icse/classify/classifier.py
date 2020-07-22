import pandas as pd

from sklearn import pipeline,ensemble,preprocessing,feature_extraction,cross_validation,metrics

train = pd.read_csv("coded_sentences.csv")

print(train.head())

clf=pipeline.Pipeline([
        ('tfidf_vectorizer', feature_extraction.text.TfidfVectorizer(lowercase=True)),
        ('rf_classifier', ensemble.RandomForestClassifier(n_estimators=500,verbose=1,n_jobs=-1))
    ])

X_train,X_test,y_train,y_test=cross_validation.train_test_split(
        train.sentence,train.Code, test_size=0.2)

clf.fit(X_train,y_train)

y_pred=clf.predict(X_test)

print(metrics.accuracy_score(y_test,y_pred))


result = pd.DataFrame({'sentence': X_test, 'actual': y_test, 'pred': y_pred})

result.loc[result["actual"] != result["pred"]].to_csv('misclass.csv', index=False)

