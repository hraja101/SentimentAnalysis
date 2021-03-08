import time

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, fbeta_score
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import GaussianNB

from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer

from tweepy import OAuthHandler, API
from tweepy.streaming import Stream
from TwitterDataStream import TweetCollection, TwitterStreamListener
import TwitterKeys
from src.TweetSentiment import TweetSentiment

classifiers = [
    ('Gaussian Naive Bayes', GaussianNB())
    , ('LinearSVC', LinearSVC(random_state=42))
    , ('SGD(SVM) classifier',
       SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, max_iter=10, random_state=42, tol=None))
    , ('Decision Tree', DecisionTreeClassifier(max_depth=5))
    , ('Random Forest (50 estimators)',
       RandomForestClassifier(n_estimators=50, n_jobs=10))
    , ('Random Forest (200 estimators)',
       RandomForestClassifier(n_estimators=200, n_jobs=10))
    , ('Logistic Regression (C=1000)',
       OneVsRestClassifier(LogisticRegression(C=10000)))
    , ('AdaBoost', OneVsRestClassifier(AdaBoostClassifier()))
]


class Classifiers:
    def __init__(self, data):
        self.data = data

    def build_linear_classification_models(self):
        x, y = self.data['tweets'], self.data['sentiment']
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=None, shuffle=True)

        for name, classifier in classifiers:
            classifier_model = make_pipeline(
                CountVectorizer(),
                TfidfTransformer(),
                FunctionTransformer(lambda x: x.todense(), accept_sparse=True),
                classifier)

            t0 = time.time()
            classifier_model.fit(x_train, y_train)
            t1 = time.time()

            classifier_prediction = classifier_model.predict(x_test)
            t2 = time.time()
            acc = accuracy_score(y_true=y_test, y_pred=classifier_prediction)
            f1 = fbeta_score(y_true=y_test, y_pred=classifier_prediction, beta=1, average="weighted")

            print("{name:<30}: {score:<5}  {f_beta} in {train_time:} /  {test_time}"
                  .format(name="Classifier",
                          score="Accuracy",
                          f_beta="f1-score",
                          train_time="training-time",
                          test_time="test-time"))
            print("-" * 88)
            print(("{name:<30}: {acc:0.4f}%  {f1:0.4f}% in {train_time:0.2f}s"
                   " training / {test_time:0.2f}s testing")
                  .format(name=name,
                          acc=(acc * 100),
                          f1=(f1 * 100),
                          train_time=t1 - t0,
                          test_time=t2 - t1))
            print("\n")


if __name__ == '__main__':

    auth = OAuthHandler(TwitterKeys.CONSUMER_API_KEY, TwitterKeys.CONSUMER_API_SECRET)
    auth.set_access_token(TwitterKeys.CONSUMER_ACCESS_TOKEN, TwitterKeys.CONSUMER_ACCESS_TOKEN_SECRET)
    track_list = ['#COVID-19', '#COVID', '#vaccine', 'india']

    # TODO- to fetch user details
    api = API(auth)

    if not api.verify_credentials():
        raise Exception('Unable to verify credentials with remote server: check your twitter API keys:')

    # create an instance of the twitter stream listener
    tweet_listener = TwitterStreamListener()

    # stream instance
    tweepy_stream: Stream = Stream(auth=auth, listener=tweet_listener)
    tweepy_stream.filter(languages=["en"], track=track_list)

    sentiment = TweetSentiment(TweetCollection)
    tweets_df = sentiment.tweetsData()

    classification = Classifiers(tweets_df)

    classification.build_linear_classification_models()
