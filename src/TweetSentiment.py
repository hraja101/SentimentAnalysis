import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from textblob import TextBlob

nltk.download('vader_lexicon')
nltk.download('stopwords')


def clean_text(text):
    """
        Parameters
        ----------
        text : tweet

        Returns
        -------
        preprocessed tweet
        :param text:
    """
    # clean up text
    stopwords_replace = set(stopwords.words('english'))
    text = text.lower()
    # preprocessing

    preprocess_tw = re.sub(r'[^\w\s]', '', text)  # remove all punctuations
    preprocess_tw = re.sub(r"http\S+", '', preprocess_tw)
    preprocess_tw = re.sub(r'\s+', ' ',
                           preprocess_tw).strip()  # remove new lines, more than two spaces with the single space
    preprocess_tw = re.sub(r'[0-9,\n]', r'', preprocess_tw)  # remove numbers
    preprocess_tw = ' '.join(word for word in preprocess_tw.split() if word not in stopwords_replace)
    return preprocess_tw


def de_emoji(text):
    # Strip all non-ASCII characters to remove emoji characters
    if text:
        return text.encode('ascii', 'ignore').decode('ascii')
    else:
        return None


def addSentiment(text):
    text_blob = TextBlob(text)
    analyzer = SentimentIntensityAnalyzer()
    text_vs = analyzer.polarity_scores(text)

    if text_blob.sentiment.polarity < 0 and text_vs['compound'] <= -0.05:
        sentiment_tweet = "negative"
    elif text_blob.sentiment.polarity > 0 and text_vs['compound'] >= 0.05:
        sentiment_tweet = "positive"
    else:
        sentiment_tweet = "neutral"

    return sentiment_tweet


class TweetSentiment:

    def __init__(self, collection):
        self.collection = collection

    def tweetsData(self):
        userid = []
        creation_time = []
        tweets = []

        data = self.collection.find({}, {'id_str': 1, 'created_at': 1, 'text': 1})
        for x in data:
            userid.append(x['id_str'])
            creation_time.append(x['created_at'])
            tweets.append(x['text'])

        tweets_emoji = [de_emoji(x) for x in tweets]
        tweets_preprocess = [clean_text(x) for x in tweets_emoji]
        tweets_sentiment = [addSentiment(x) for x in tweets_preprocess]
        datadict = {'userid': userid, 'creation_time': creation_time,
                    'tweets': tweets_preprocess, 'sentiment': tweets_sentiment}

        tweets_dataframe = pd.DataFrame(data=datadict)

        return tweets_dataframe

