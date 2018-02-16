import os
import re
import pdb
import praw
import pickle
import tweepy
import logging
from configparser import ConfigParser


class SummonBot(object):

    def __init__(self, config_file, ini_module):
        self.logger = logging.getLogger('summon_bot')
        self.logger.setLevel(logging.INFO)
        self.summon_log = logging.FileHandler('summon.log')
        self.summon_log.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)-12s: %(levelname)-8s %(message)s')
        self.summon_log.setFormatter(self.formatter)
        self.logger.addHandler(self.summon_log)
        self.config_file = config_file
        self.config = ConfigParser()
        self.config.read(config_file)
        self.ini_module = ini_module
        self.config_dict = {
            'consumer_key': self.config.get(self.ini_module, 'key'),
            'consumer_secret': self.config.get(self.ini_module, 'secret'),
            'token_key': self.config.get(self.ini_module, 'token_key'),
            'token_secret': self.config.get(self.ini_module, 'token_secret'),
            'last_tweet_file': self.config.get(self.ini_module, 'last_tweet_file'),
            'replied_file': self.config.get(self.ini_module, 'replied_file'),
            'praw_config': self.config.get(self.ini_module, 'praw_config'),
            'subreddit': self.config.get(self.ini_module, 'subreddit'),
            'search_str': self.config.get(self.ini_module, 'search_str'),}


    def load_replied_comments(self):
        self.replied_file = self.config_dict.get('replied_file')
        if not os.path.isfile(self.replied_file):
            self.replied_comments = []
        else:
            self.replied_comments = pickle.load(open(self.replied_file, 'rb'))
        message = 'Loaded comments previously replied to'
        logging.info(message)
        return self.replied_comments


    def load_last_tweet(self):
        pickle_file = self.config_dict.get('last_tweet_file')
        if not os.path.isfile(pickle_file):
            self.last_tweet = ""
        else:
            self.last_tweet = pickle.load(open(pickle_file, 'rb'))
        message = 'Loaded last tweet id'
        logging.info(message)
        return self.last_tweet


    def tweets(self):
        auth = tweepy.OAuthHandler(self.config_dict.get('consumer_key'),
                                   self.config_dict.get('consumer_secret'))
        auth.set_access_token(self.config_dict.get('token_key'),
                              self.config_dict.get('token_secret'))
        api = tweepy.API(auth)
        user = api.get_user("ebooks_goetia")
        last_tweet = self.load_last_tweet()
        if last_tweet:
            timeline = api.user_timeline(user.id, max_id=last_tweet)
            timeline = timeline[1::]
        else:
            timeline = api.user_timeline(user.id)
        message_a = 'Loaded user timeline'
        message_b = 'Generated single tweet'
        logging.info(message_a)
        for self.tweet in timeline:
            if "RT" not in self.tweet.text:
                yield self.tweet
                logging.info(message_b)
            else:
                pass


    def parse_tweet(self, tweet):
        image_url = tweet.entities['media'][0]['media_url']
        ascii_tweet = tweet.text.encode('ascii', 'ignore')
        ascii_tweet = re.sub(r"http\S+", "", ascii_tweet)
        name = '{0} {1}'.format(ascii_tweet.split(' ')[2],
                                ascii_tweet.split(' ')[3].replace(',', ''))
        attributes = [x.strip() for x in ascii_tweet.split('\n')[1::]]
        attributes = ", ".join(attributes)

        reply_str = "You have summoned [{0}]({1}) Demon of: {2}"
        self.reply = reply_str.format(name, image_url, attributes)
        logging.info(self.reply)
        return self.reply


    def reply_post(self, comment, tweets):
        if tweets:
            tweet = next(tweets)
        else:
            tweets = self.tweets()
            tweet = next(tweets)
        reply = self.parse_tweet(tweet)
        comment.reply(reply)
        last_tweet = tweet.id
        self.replied_comments.append(comment.id)
        last_tweet_file = self.config_dict.get('last_tweet_file')
        replied_file = self.config_dict.get('replied_file')
        pickle.dump(last_tweet, open(last_tweet_file, 'wb'))
        pickle.dump(self.replied_comments, open(replied_file, 'wb'))
        logging.info('Comment replied')


    def summon(self):
        reddit = praw.Reddit(self.config_dict.get('praw_config'))
        subreddit = reddit.subreddit(self.config_dict.get('subreddit'))
        tweets = self.tweets()
        replied_comments = self.load_replied_comments()

        for comment in subreddit.stream.comments():
            logging.info('Checking comment: {0}'.format(comment.id))
            search = re.search(self.config_dict.get('search_str'),
                               comment.body,
                               re.IGNORECASE)
            if comment.id not in replied_comments and search:
                logging.info('Replying to comment: {0}'.format(comment.id))
                self.reply_post(comment, tweets)
            else:
                pass


def main():

    necromancer = SummonBot('bot.ini', 'api_settings')

    try:
        necromancer.summon()

    except KeyboardInterrupt:
        print('Bot has been shutdown')

if __name__ == '__main__':
    main()
