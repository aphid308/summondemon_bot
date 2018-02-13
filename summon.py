#!/home/drowns/summondemon/summondemon_env/bin/python
import os
import tweepy
import praw
import pdb
import pickle
import re
from configparser import ConfigParser
import logging
from datetime import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                   level=logging.DEBUG,
                   filename='summon.log',)


def summon():
    config = ConfigParser()
    config.read('twitter.ini')

    CONSUMER_KEY = config.get('api_settings', 'key')
    CONSUMER_SECRET = config.get('api_settings', 'secret')
    TOKEN_KEY = config.get('api_settings', 'token_key')
    TOKEN_SECRET = config.get('api_settings', 'token_secret')

    twitter_auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    twitter_auth.set_access_token(TOKEN_KEY, TOKEN_SECRET)
    twitter_api = tweepy.API(twitter_auth)
    lesser_bot = twitter_api.get_user("ebooks_goetia")

    reddit = praw.Reddit('bot1')
    subreddit = reddit.subreddit("test")

    for comment in subreddit.stream.comments():
            replied_comments, last_tweet = load_persistent()
            search = re.search("/u/summondemon", comment.body, re.IGNORECASE)

            if comment.id not in replied_comments and search:
                if last_tweet:
                    timeline = twitter_api.user_timeline(lesser_bot.id, max_id=last_tweet)
                    timeline = timeline[1::]
                else:
                    timeline = twitter_api.user_timeline(lesser_bot.id)

                tweet = timeline.pop()
                image_url = tweet.entities['media'][0]['media_url']
                ascii_tweet = tweet.text.encode("ascii", "ignore")
                ascii_tweet = re.sub(r"http\S+", "", ascii_tweet)
                name = "{0} {1}".format(ascii_tweet.split(' ')[2],
                                        ascii_tweet.split(' ')[3].replace(',', ''))
                attributes = [x.strip() for x in ascii_tweet.split("\n")[1::]]
                attributes = ", ".join(attributes)

                reply_str = "You have summoned [{0}]({1}) Demon of: {2}"
                reply = reply_str.format(name, image_url, attributes)
                comment.reply(reply)

                logging.info("replied to comment id " + comment.id + " with " + reply)

                last_tweet = tweet.id
                replied_comments.append(comment.id)
                save_persistent(replied_comments, last_tweet)

            elif comment.id in replied_comments and search:
                logging.info("We have already replied to comment " + comment.id)

            else:
                pass

def load_persistent():
    if not os.path.isfile('last_tweet.p'):
        last_tweet = ""
    else:
        last_tweet = pickle.load(open('last_tweet.p', 'rb'))

    if not os.path.isfile('replied_comments.p'):
        replied_comments = []
    else:
        replied_comments = pickle.load(open('replied_comments.p', 'rb'))

    return (replied_comments, last_tweet)

def save_persistent(replied_comments, last_tweet):
    pickle.dump(last_tweet, open("last_tweet.p", "wb"))
    pickle.dump(replied_comments, open("replied_comments.p", "wb"))

def main():
    try:
        summon()
    except KeyboardInterrupt:
        logging.info("Administrator has powered down the bot.")

if __name__ == '__main__':
    main()
