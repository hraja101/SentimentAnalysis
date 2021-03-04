import json
import re
import sys
import time
from random import randrange

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from tweepy import OAuthHandler, API
from tweepy.streaming import StreamListener, Stream

import TwitterKeys

IS_PY3 = sys.version_info >= (3, 0)

if not IS_PY3:
    print("Sorry, requires Python 3.")
    sys.exit(1)

MONGO_HOST = 'mongodb://localhost/twitterSentiment'
blacklist = [
    '[document]',
    'noscript',
    'header',
    'html',
    'meta',
    'head',
    'input',
    'script',
    'style',
    '/n'
]


# Override the stream class
class TwitterStreamListener(StreamListener):

    def __init__(self):
        self.count = 0
        self.max_count = 100  # max 8000 tweets
        self.mongoClient = MongoClient(MONGO_HOST)

    def on_data(self, raw_data):
        try:
            raw_data
        except TypeError:
            print("Completed:")

        else:
            try:
                # Use or create a twitterDB
                twitterDB = self.mongoClient.twitterSentiment
                collection = twitterDB.tweetSentiment
                twitter_data_dict = json.loads(raw_data)

                if twitter_data_dict['retweeted'] or 'RT @' in twitter_data_dict['text']:
                    return
                twitter_data_text = twitter_data_dict["text"]
                collection.insert(twitter_data_dict)
                self.count += 1

                if twitter_data_text is None:
                    return True  # continue with next data stream

                if self.count == self.max_count:

                    print(self.count, ": tweets reached", "expected maximum tweets:", self.max_count)
                    return False  # disconnect stream ?

                else:
                    tweet_urls = re.findall(
                        r'(http[s]?://(?!twitter)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
                        , twitter_data_text)

                    for url in tweet_urls:
                        try:
                            output = ''
                            response = requests.get(url)

                            if 'https://twitter.com' in response.url:
                                pass
                            else:
                                html_page = response.content
                                time.sleep(randrange(1, 5))
                                soup = BeautifulSoup(html_page, 'html.parser')
                                text = soup.find_all(text=True)
                                for t in text:
                                    if t.parent.name not in blacklist:
                                        output += '{} '.format(t)
                                print('url:', response.url, 'content:', output)

                                Query = {"text": twitter_data_text}
                                values = {"$set": {"text": twitter_data_text+output}}

                                collection.update_one(Query, values)
                                cursor = collection.find()
                                for record in cursor:
                                    print(record)

                        except Exception:
                            print(url)

            except KeyError:
                return True  # continue if there is no text

    # on failure
    def on_error(self, status_code):
        time.sleep(randrange(2, 30))
        return True

    # on timeout
    def on_timeout(self):
        time.sleep(randrange(2, 30))
        return True


if __name__ == '__main__':

    auth = OAuthHandler(TwitterKeys.CONSUMER_API_KEY, TwitterKeys.CONSUMER_API_SECRET)
    auth.set_access_token(TwitterKeys.CONSUMER_ACCESS_TOKEN, TwitterKeys.CONSUMER_ACCESS_TOKEN_SECRET)
    track_list = ['#COVID-19', '#COVID', '#vaccine']

    # TODO- to fetch user details
    api = API(auth)

    if not api.verify_credentials():
        raise Exception('Unable to verify credentials with remote server: check your twitter API keys:')

    # create an instance of the twitter stream listener
    tweet_listener = TwitterStreamListener()

    # stream instance
    tweepy_stream: Stream = Stream(auth=auth, listener=tweet_listener)

    tweepy_stream.filter(languages=["en"], track=track_list)
