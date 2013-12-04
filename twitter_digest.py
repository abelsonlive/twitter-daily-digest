#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import tweepy
from datetime import datetime, timedelta
import pystmark
import yaml
import pytz

CONFIG = yaml.safe_load(open('config.yml'))

def tz_adj(dt):
  tz = "America/New_York"
  utc = pytz.timezone("UTC")
  mytz = pytz.timezone(tz)
  try:
      dt = dt.replace(tzinfo=utc)
  except:
      return None
  else:
      return mytz.normalize(dt.astimezone(mytz))

def one_day_ago():
  mytz = pytz.timezone("America/New_York")
  return datetime.now().replace(tzinfo=mytz) - timedelta(days=1)

class TwitterArchive(object):

  def __init__(self, screen_name):
  
    # twitter
    self.screen_name = screen_name
    self.one_day_ago = one_day_ago()
    self.consumer_key = CONFIG["consumer_key"]
    self.consumer_secret = CONFIG["consumer_secret"]
    self.access_token = CONFIG["access_token"]
    self.access_token_secret = CONFIG["access_token_secret"]
    self.postmark_api_key = CONFIG["postmark_api_key"]
    self.email_to = CONFIG["email_to"]
    self.email_from = CONFIG["email_from"]
    self.api = self.connect_to_twitter()


  def connect_to_twitter(self):
    # authenticate
    auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
    auth.set_access_token(self.access_token, self.access_token_secret)
    api = tweepy.API(auth)
    return api


  # gmail helper
  def send_email(self, message, subject):
    message = message.decode('utf-8', errors="ignore")
    msg = pystmark.Message(sender=self.email_from, 
                           to=self.email_to, 
                           subject=subject,
                           html=message, 
                           tag="daily-twitter-digest")
    response = pystmark.send(msg, api_key=self.postmark_api_key)
    try:
      response.raise_for_status()
    except Exception as e:
      print e.message


  def format_tweet(self, t):
    try:
      text = t.text.decode('utf-8', errors="ignore")
    except:
      return None
    else:
      name = t.user.screen_name
      img_url = t.user.profile_image_url
      prof_url = "http://twitter.com/%s/" % name
      tweet_url = "http://twitter.com/%s/status/%s" % (name, t.id_str)
      date = tz_adj(t.created_at)

      if date > self.one_day_ago:

        # format date
        date = date.strftime('%Y-%m-%d %H:%M:%S')

        # reformat urls
        urls = t.entities['urls']
        for url in urls:
          if url.has_key('url'):
            text = re.sub(
              url['url'], 
              "<a href='%s' target='_blank'>%s</a>" % (url['url'], url['expanded_url']), 
              text
            )
        
        message = '''
                      <a href="%s" target="_blank"><img width="75px" src="%s"> <b> %s </b> </a>
                      <br></br>
                        %s
                      <br></br>
                      <a href="%s" target="_blank">%s</a> 
                  ''' % (prof_url, img_url, name, text, tweet_url, date)

        return message

      else:
        print "out of range..."
        return None


  def format_message(self, tweets):
    messages = []
    for t in tweets:
      message = self.format_tweet(t)
      if message is not None:
        messages.append(message.decode('utf-8', errors="ignore"))


    return "<hr></hr>".join([m for m in messages if m is not None])


  def grab_tweets(self):
    tweets = []
    for p in range(1, 2):
      these_tweets = self.api.home_timeline(
        screen_name=self.screen_name, 
        page=p, 
        count=200,
      )
      tweets.extend(these_tweets)

    return tweets


  def run(self):
    datestring = datetime.now().strftime("%m/%d/%y - %H %p")
    subject = "Twtitter Digest - %s" % datestring
    tweets = self.grab_tweets()
    print "found %d tweets" % len(tweets)
    message = "<h1>" + subject + "</h1><hr></hr>" + self.format_message(tweets)
    self.send_email(message, subject)

if __name__ == '__main__':
  ta = TwitterArchive("thenedders")
  ta.run()
