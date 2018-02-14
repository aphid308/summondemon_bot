#!/home/drowns/summondemon/summondemon_env/bin/python
import os
import tweepy
import praw
import pdb
import pickle
import re
from configparser import ConfigParser
import logging


def load_persistent(pickle_file):
    if not os.path.isfile(pickle_file):
        replied_comments = []
    else:
        replied_comments = pickle.load(open(pickle_file, 'rb'))

    return replied_comments

def load_last_tweet(pickle_file):
    if not os.path.isfile(pickle_file):
        last_tweet = ""
    else:
        last_tweet = pickle.load(open(pickle_file, 'rb'))
    return last_tweet

def get_tweet():
    config = ConfigParser()
    config.read('twitter.ini')

    CONSUMER_KEY = config.get('api_settings', 'key')
    CONSUMER_SECRET = config.get('api_settings', 'secret')
    TOKEN_KEY = config.get('api_settings', 'token_key')
    TOKEN_SECRET = config.get('api_settings', 'token_secret')

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(TOKEN_KEY, TOKEN_SECRET)
    api = tweepy.API(auth)
    lesser_bot = api.get_user("ebooks_goetia")
    last_tweet = load_last_tweet('last_tweet.p')
    if last_tweet:
        timeline = api.user_timeline(lesser_bot.id, max_id=last_tweet)
        timeline = timeline[1::]
    else:
        timeline = api.user_timeline(lesser_bot.id)

    for tweet in timeline:
        if "RT" not in tweet.text:
            logging.info("suitable tweet ({0}) found".format(tweet.id))
            yield tweet
        else:
            pass

def parse_tweet(tweet):
    image_url = tweet.entities['media'][0]['media_url']
    ascii_tweet = tweet.text.encode("ascii", "ignore")
    ascii_tweet = re.sub(r"http\S+", "", ascii_tweet)
    name = "{0} {1}".format(ascii_tweet.split(' ')[2],
                            ascii_tweet.split(' ')[3].replace(',', ''))
    attributes = [x.strip() for x in ascii_tweet.split("\n")[1::]]
    attributes = ", ".join(attributes)

    reply_str = "You have summoned [{0}]({1}) Demon of: {2}"
    logging.info("reply parsed: {0}".format(reply_str))
    reply = reply_str.format(name, image_url, attributes)
    return reply


def summon():

    reddit = praw.Reddit('bot1')
    subreddit = reddit.subreddit("test")
    tweets = get_tweet()
    replied_comments = load_persistent('replied_comments.p')

    for comment in subreddit.stream.comments():
        search = re.search("/u/summondemon", comment.body, re.IGNORECASE)

        if comment.id not in replied_comments and search:
            tweet = next(tweets)
            reply = parse_tweet(tweet)
            logging.info(reply)
            comment.reply(reply)
            logging.info("setting {0} as last tweet".format(tweet.id))
            last_tweet = tweet.id
            logging.info("adding {0} to replied comments".format(comment.id))
            replied_comments.append(comment.id)
            pickle.dump(last_tweet, open('last_tweet.p', 'wb'))
            pickle.dump(replied_comments, open('replied_comments.p', 'wb'))
            logging.info("persistent data saved")

        elif comment.id in replied_comments and search:
            logging.info("We have already replied to comment " + comment.id)

        else:
            pass

def main():

    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                       level=logging.INFO,
                       filename='summon.log',)
    try:
        summon()
    except KeyboardInterrupt:
        logging.info("Administrator has powered down the bot.")

if __name__ == '__main__':
    main()
