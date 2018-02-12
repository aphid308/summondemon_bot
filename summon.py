#!/home/drowns/summondemon/summondemon_env/bin/python

import os
import tweepy
import praw
import pdb
import pickle
import re
from configparser import ConfigParser

#setup twitter credentials
#move to config file before production
config = ConfigParser()
config.read('twitter.ini')
CONSUMER_KEY = config.get('api_settings', 'key')
CONSUMER_SECRET = config.get('api_settings', 'secret')
TOKEN_KEY = config.get('api_settings', 'token_key')
TOKEN_SECRET = config.get('api_settings', 'token_secret')

#instantiate twitter api object
twitter_auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
twitter_auth.set_access_token(TOKEN_KEY, TOKEN_SECRET)
twitter_api = tweepy.API(twitter_auth)

#instantiate reddit client
reddit = praw.Reddit('bot1')

#setup the subreddit and username to listen for
subreddit_id = "test"
trigger = "/u/summondemon"

#setup the twitter user
lesser_bot = twitter_api.get_user("ebooks_goetia")

#create the subredit object
subreddit = reddit.subreddit(subreddit_id)

def main():

    for comment in subreddit.stream.comments():
        replied_comments, last_tweet = load_persistent()
        if comment.id not in replied_comments and re.search(trigger,
                                                            comment.body,
                                                            re.IGNORECASE):
            if last_tweet:
                timeline = twitter_api.user_timeline(lesser_bot.id, max_id=last_tweet)
                timeline = timeline[1::]
            else:
                timeline = twitter_api.user_timeline(lesser_bot.id)

            #get the next tweet in the list
            tweet = timeline.pop()
            #extract image url from tweet
            image_url = tweet.entities['media'][0]['media_url']
            #convert tweet to ascii
            ascii_tweet = tweet.text.encode("ascii", "ignore")
            #remove the url from the end
            ascii_tweet = re.sub(r"http\S+", "", ascii_tweet)
            #extract the demon's title
            title = ascii_tweet.split(" ")[2]
            #extract the demon's name
            name = ascii_tweet.split(" ")[3].replace(",", "")
            #extract the attributes, remove whitespace and format
            attributes = [x.strip() for x in ascii_tweet.split("\n")[1::]]
            attributes = ", ".join(attributes)
            #setup the string template for our reply
            reply_str = "You have summoned [{0} {1}]({2}) Demon of: {3}"
            #format the template with values
            reply = reply_str.format(title, name, image_url, attributes)
            #post reply
            comment.reply(reply)
            print("replied to comment id " + comment.id + " with " + reply)
            #store value for last tweet
            last_tweet = tweet.id
            #store value for comments that have been replied to
            replied_comments.append(comment.id)
            save_persistent(replied_comments, last_tweet)
        elif comment.id in replied_comments and re.search(trigger,
                                                          comment.body,
                                                          re.IGNORECASE):
            print("We have already replied to comment " + comment.id)
        else:
            pass

def load_persistent():
    #if pickle file does not exist, create the last tweet variable
    #if it does, load the variable from the pickle file
    if not os.path.isfile('last_tweet.p'):
        last_tweet = ""
    else:
        last_tweet = pickle.load(open('last_tweet.p', 'rb'))

    #if pickle file does not exist, create the list of replied comments
    #if it does load the list from the pickle file
    if not os.path.isfile('replied_comments.p'):
        replied_comments = []
    else:
        replied_comments = pickle.load(open('replied_comments.p', 'rb'))

    return (replied_comments, last_tweet)

def save_persistent(replied_comments, last_tweet):
    #save comments replied to and last tweet id to pickle files
    pickle.dump(last_tweet, open("last_tweet.p", "wb"))
    pickle.dump(replied_comments, open("replied_comments.p", "wb"))


if __name__ == '__main__':
    main()
