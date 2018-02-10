#!/home/drowns/summondemon/summondemon_env/bin/python

import praw
import pdb
import pickle
import re
import tweepy
import os

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

#setup twitter credentials
#move to config file before production
twitter_key = os.environ['KEY']
twitter_secret = os.environ["SECRET"]
twitter_token_key = os.environ["TOKEN_KEY"]
twitter_token_secret = os.environ["TOKEN_SECRET"]

#instantiate twitter api object
twitter_auth = tweepy.OAuthHandler(twitter_key, twitter_secret)
twitter_auth.set_access_token(twitter_token_key, twitter_token_secret)
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

#if there is a value for last tweet instantiate the timeline
#with only tweets that are older than the last tweet used
if last_tweet:
    timeline = twitter_api.user_timeline(lesser_bot.id, max_id=last_tweet)
    timeline = timeline[1::]
#if there is no value just start at the newest tweet
else:
    timeline = twitter_api.user_timeline(lesser_bot.id)

for submission in subreddit.hot(limit=10):
    submission.comments.replace_more(limit=0)
    submission.comments_sort = 'new'
    flattened_comments = submission.comments.list()
    for comment in flattened_comments:
        if comment.id not in replied_comments and re.search(trigger,
                                                            comment.body,
                                                            re.IGNORECASE):
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
        elif comment.id in replied_comments and re.search(trigger,
                                                          comment.body,
                                                          re.IGNORECASE):
            print("We have already replied to comment " + comment.id)
        else:
            print("You were not mentioned")

#save comments replied to and last tweet id to pickle files
pickle.dump(last_tweet, open("last_tweet.p", "wb"))
pickle.dump(replied_comments, open("replied_comments.p", "wb"))
