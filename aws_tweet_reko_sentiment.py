import tweepy
import json
import os 
import urllib.request
import datetime
import boto3
from collections import Counter

class TwitterStreamHandler():
    def __init__(self):
        self.twitter_access_token = None
        self.twitter_access_token_secret = None
        self.twitter_consumer_key = None
        self.twitter_consumer_secret = None
        self.twitter_filters_list = None
        self.twitter_languages_list = None

    def FetchLastPictures(self):
        stream_callback = FetchedPictureHandler()
        auth = tweepy.OAuthHandler(self.twitter_consumer_key, self.twitter_consumer_secret)
        auth.set_access_token(self.twitter_access_token, self.twitter_access_token_secret)  
        stream = tweepy.Stream(auth, stream_callback,timeout=120)
        stream.filter(languages=self.twitter_languages_list ,track=self.twitter_filters_list)


class FetchedPictureHandler(tweepy.StreamListener):
    def on_data(self, data):
        global NUMBER_OF_FETCHED_PICTURES
        if NUMBER_OF_FETCHED_PICTURES < NUMBER_OF_PICTURE_TO_FECTH:
            try:
                decoded = json.loads(data)
                if 'extended_entities' in decoded:
                    for media in decoded['extended_entities']['media']:
                        pic_url = media['media_url_https']
                        pic_name = '{}{}_{}'.format(IMG_OUTPUT_LOCATION, datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f"), os.path.basename(pic_url))
                        urllib.request.urlretrieve(pic_url, pic_name)
            
                        #check if is there a face within the picture
                        p = open(pic_name, 'rb')
                        reko_response = rekognition_client_connection.detect_faces(Image={
                                                                            'Bytes':bytearray(p.read())
                                                                        },
                                                                            Attributes=[
                                                                            'ALL'
                                                                        ])
                        p.close()
                        if 'FaceDetails' in reko_response and len(reko_response['FaceDetails'])>0:
                            for detail in reko_response['FaceDetails']:
                                #store details
                                if 'Smile' in detail:
                                    SMILES.append(detail['Smile']['Value'])
                                if 'Gender' in detail:
                                    GENDERS.append(detail['Gender']['Value'])

                                if 'Emotions' in detail:
                                    for e in detail['Emotions']:
                                        if e['Type'] not in EMOTIONS:
                                            EMOTIONS[e['Type']] = []
                                        EMOTIONS[e['Type']].append(e['Confidence'])

                            NUMBER_OF_FETCHED_PICTURES = NUMBER_OF_FETCHED_PICTURES + 1
                        else:
                            os.remove(pic_name)
            except Exception as e:
                print(e)
                pass
            return True
        else:
            return False

    def on_error(self, status):
        # TODO maybe add some log?
        print(status)

AWS_ACCESS_KEY = ''
AWS_SECRET_ACCESS_KEY =''
rekognition_client_connection = boto3.client(
    'rekognition',
    aws_access_key_id = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name = 'eu-west-1'
)


NUMBER_OF_FETCHED_PICTURES = 0
NUMBER_OF_PICTURE_TO_FECTH = 25 # number of iamges to download
IMG_OUTPUT_LOCATION = 'img_out/' # output folder

SMILES = []
GENDERS = []
EMOTIONS = {}

if __name__ == '__main__':
    try:
        tw_handler = TwitterStreamHandler()
        tw_handler.twitter_access_token = ""
        tw_handler.twitter_access_token_secret = ""
        tw_handler.twitter_consumer_key = ""
        tw_handler.twitter_consumer_secret = ""
        tw_handler.twitter_filters_list = ['#christmas', '#family', '#friends', '#love', '#faces'] # set of filters
        tw_handler.twitter_languages_list = ['en']
        tw_handler.FetchLastPictures()

		# print the output
        print("SMILING:")
        for i,j in zip(Counter(SMILES).keys(), Counter(SMILES).values()):
            print('{} : {}'.format(i, j))
        
        print("GENDER:")
        for i,j in zip(Counter(GENDERS).keys(), Counter(GENDERS).values()):
            print('{} : {}'.format(i, j))
        
        print("EMOTIONS:")
        for key, value in EMOTIONS.items():
            print('{} : {}'.format(key, sum(value) / float(len(value))))

    except Exception as e:
        print(e)
