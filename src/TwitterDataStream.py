import json
import re
import sys
import time
from random import randrange

import requests
from requests.exceptions import ConnectionError, RetryError, \
    SSLError, HTTPError, ConnectTimeout, TooManyRedirects, InvalidHeader
from bs4 import BeautifulSoup
from pymongo import MongoClient
from requests.models import Response

from tweepy.streaming import StreamListener
import socket
from socket import gaierror


IS_PY3 = sys.version_info >= (3, 0)

if not IS_PY3:
    print("Sorry, requires Python 3.")
    sys.exit(1)

# Use or create a twitterDB
MONGO_HOST = 'mongodb://localhost/twitterSentiment'
mongoClient = MongoClient(MONGO_HOST)
twitterDB = mongoClient.twitterSentiment
TweetCollection = twitterDB.tweetSentiment


# Override the stream class
class TwitterStreamListener(StreamListener):
    blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style', '/n']

    def __init__(self):
        self.count = 0
        self.max_count = 150  # max 300 tweets

    def on_data(self, raw_data):
        try:
            # if TweetCollection.find({}, {"text": 1}):
            #     return False
            # else:
            raw_data
        except TypeError:
            print("Completed:")

        else:
            try:
                twitter_data_dict = json.loads(raw_data)

                if twitter_data_dict['retweeted'] or 'RT @' in twitter_data_dict['text']:
                    return
                twitter_data_text = twitter_data_dict["text"]
                TweetCollection.insert_one(twitter_data_dict)
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
                            time.sleep(randrange(2, 10))
                            response: Response = requests.get(url)
                            print('tweet No:', self.count, 'url',  response.url)

                        except socket.error:
                            print("connection refused:", requests.get(url, verify=False).url)
                            continue

                        except requests.packages.urllib3.exceptions.MaxRetryError as e:
                            print(str(e))
                            continue

                        except requests.ConnectionError as e:
                            print(
                                "OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details "
                                "given below.\n")
                            print(str(e))
                            continue

                        except requests.Timeout as e:
                            print("OOPS!! Timeout Error")
                            print(str(e))
                            continue

                        except ConnectionError as e:
                            print("OOPS!! connection Error")
                            print(str(e))
                            continue

                        except SSLError as e:
                            print("OOPS!! SSL Error")
                            print(str(e))
                            continue

                        except RetryError as e:
                            print("OOPS!! retry Error")
                            print(str(e))
                            continue

                        except HTTPError as e:
                            print("OOPS!! http Error")
                            print(str(e))
                            continue

                        except gaierror as e:
                            print("OOPS!! gai Error")
                            print(str(e))
                            continue

                        except OSError as e:
                            print("os error, connection refused")
                            print(str(e))
                            continue

                        except ConnectTimeout as e:
                            print("os error, connection refused")
                            print(str(e))
                            continue

                        except TooManyRedirects as e:
                            print("os error, connection refused")
                            print(str(e))
                            continue

                        except InvalidHeader as e:
                            print("os error, connection refused")
                            print(str(e))
                            continue

                        else:
                            output = ''
                            if 'https://twitter.com' in response.url:
                                pass
                            else:
                                html_page = response.content
                                soup = BeautifulSoup(html_page, 'html.parser')
                                text = soup.find_all(text=True)
                                for t in text:
                                    if t.parent.name not in TwitterStreamListener.blacklist:
                                        output += '{} '.format(t)
                                Query = {"text": twitter_data_text}
                                values = {"$set": {"text": twitter_data_text + output}}
                                TweetCollection.update_one(Query, values)

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



