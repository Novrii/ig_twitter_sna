import tweepy
import csv
import pandas as pd
####input your credentials here
consumer_key = 'wM6OvboeX8ltdz0lYO4ksVNMn'
consumer_secret = 'VfHaFlyslESO4TEmrIaLVpNk8td6cvsPO0bGEFZwPgGRGqnMKE'
access_token = '1102773975317266433-B45cR5qbRr2SK3KuSK3LrMqvpw3Ikr'
access_token_secret = 'YEOTKGhezo2zxZNKZ4Mr6pkALOk8jqwZv59d877dADie6'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)
#####United Airlines
# Open/Create a file to append data
csvFile = open('ua.csv', 'a')
# Use csv Writer
csvWriter = csv.writer(csvFile)
# Use txt Writer
txtWriter = open('ua.txt', 'a')

for tweet in tweepy.Cursor(api.search,q="#unitedAIRLINES",count=100,
                        lang="en",
                        since="2019-04-03").items():
    print (tweet.created_at, tweet.text)
    csvWriter.writerow([tweet.created_at, tweet.text.encode('utf-8')])
    txtWriter.write([tweet.created_at, tweet.text.encode('utf-8')])