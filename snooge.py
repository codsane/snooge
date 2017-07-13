from gfycat.client import GfycatClient
from praw.models import Submission
import urllib.request
import configparser
import youtube_dl
import requests
import praw
import sys
import os
import re

class Snooge:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.txt")

        self.client_id = config.get("configuration", "client_id")
        self.client_secret = config.get("configuration", "client_secret")
        self.password = config.get("configuration", "password")
        self.username = config.get("configuration", "username")

        self.totalFailed = 0
        self.user_agent = 'Script to download saved NSFW posts by /u/codsane (https://github.com/codsane/snooge)'
        self.blacklist = ['youtube.com', 'youtu.be', 'liveleak.com', 'eroshare.com', 'streamable.com', 'np.reddit.com', 'reddit.com', 'm.reddit.com', 'bangbush.xyz']
        self.extensions = ['.jpg', '.png', '.jpeg', '.mp4', '.gif']

    def grab(self):
        self.auth()
        self.get()

    def auth(self):
        self.reddit = praw.Reddit(client_id=self.client_id, client_secret=self.client_secret, password=self.password, user_agent=self.user_agent, username=self.username)
        try:
            print('Successfully logged in as: ' + str(self.reddit.user.me()))
        except:
            print('Unable to log in to Reddit - check your credentials')
            sys.exit()
        try:
            self.dest = sys.argv[1]
        except:
            self.dest = str(self.reddit.user.me())

    def get(self):
        self.numSavedPosts = 0
        numComments = 0
        numSFW = 0
        numSelfPosts = 0
        numBlacklisted = 0

        self.domains = []
        self.saved = []

        if not os.path.exists('saved.txt'):
            open('saved.txt', 'w').close()

        print('Getting all saved posts...')
        savedPosts = self.reddit.user.me().saved(limit=None)
        for post in savedPosts:
            if not self.alreadySaved(post.id):
                self.addToSaved(post.id)
                self.numSavedPosts+=1
                if isinstance(post, Submission):
                    if post.over_18:
                        if not post.is_self:
                            if post.domain not in self.blacklist:
                                self.saved.append(post)
                                if post.domain not in self.domains:
                                    self.domains.append(post.domain)
                            else:
                                numBlacklisted+=1
                        else:
                            numSelfPosts+=1
                    else:
                        numSFW+=1
                else:
                    numComments+=1
        if self.numSavedPosts == 0:
            print('No new saved posts - delete saved.txt if you need to re-download previous posts')
            sys.exit()
        print('Grabbed ' + str(self.numSavedPosts) + ' saved posts')
        if numComments > 0:
            if numComments == 1:
                print('\tRemoved ' + str(numComments) + ' comment')
            else:
                print('\tRemoved ' + str(numComments) + ' comments')
        if numSFW > 0:
            if numSFW == 1:
                print('\tRemoved ' + str(numSFW) + ' safe for work post')
            else:
                print('\tRemoved ' + str(numSFW) + ' safe for work posts')
        if numSelfPosts > 0:
            if numSelfPosts == 1:
                print('\tRemoved ' + str(numSelfPosts) + ' self post')
            else:
                print('\tRemoved ' + str(numSelfPosts) + ' self posts')
        if numBlacklisted > 0:
            if numBlacklisted == 1:
                print('\tRemoved ' + str(numBlacklisted) + ' post from blacklisted domains')
            else:
                print('\tRemoved ' + str(numBlacklisted) + ' posts from blacklisted domains')
        print(str(len(self.saved)) + ' total posts:')
        self.savedDict = {}
        for domain in self.domains:
            self.savedDict[domain] = []
        for post in self.saved:
            self.savedDict[post.domain].append(post.url)
        for domain, posts in self.savedDict.items():
            print('\t' + str(len(posts)) + ' ' + domain + ' posts')

    def save(self):
        if not os.path.exists(self.dest):
            os.makedirs(self.dest)

        self.findRawExtensions()
        if len(self.saved) - len(self.linksToSave) > 0:
            self.saveRemaining()

        print()
        print('Total posts saved: ' + str(len(self.saved) - self.totalFailed))
        if self.totalFailed > 0:
            print('Unable to save: ' + str(self.totalFailed) + ' total posts')

    def findRawExtensions(self):
        print('Checking posts for raw files (links ending in .jpg/.gif/.mp4/etc)')
        self.linksToSave = []

        for domain, posts in self.savedDict.items():
            for post in posts:
                if any(ext in post.split('/')[-1] for ext in self.extensions):
                    if '.gifv' not in post.split('/')[-1]:
                        self.linksToSave.append(post)

        for link in self.linksToSave:
            for key in self.savedDict:
                try:
                    self.savedDict[key].remove(link)
                except:
                    continue

        keysToRemove = []
        for domain, posts in self.savedDict.items():
            if len(posts) == 0:
                keysToRemove.append(domain)
        for key in keysToRemove:
            self.savedDict.pop(key, None)

        print('\tFound ' + str(len(self.linksToSave)) + ' raw files to save')
        if len(self.linksToSave) > 0:
            print('Attempting to save ' + str(len(self.linksToSave)) + ' files from raw links...')

            failedSave = []
            for link in self.linksToSave:
                try:
                    urllib.request.urlretrieve(link,
                                               self.dest + '/' + link.split('/')[-1].replace('?1', ''))
                except:
                    failedSave.append(link)

            if len(failedSave) > 0:
                print('\tError saving ' + str(len(failedSave)) + ' files:')
                for fail in failedSave:
                    print('\t' + fail)
            print('\tSuccessfully saved ' + str(len(self.linksToSave) - len(failedSave)) + ' files')

    def saveRemaining(self):
        print('Attempting to save ' + str(len(self.saved) - len(self.linksToSave)) + ' remaining posts')
        unableToSave = []
        for domain in self.savedDict:
            if domain == 'gfycat.com':
                self.saveGfycats(self.savedDict[domain])
            elif (domain == 'imgur.com') or (domain == 'm.imgur.com'):
                self.saveImgurAlbums(self.savedDict[domain])
            else:
                self.tryYouTubeDownload(domain, self.savedDict[domain])

        print('Saved files from ' + str(len(self.saved) - len(self.linksToSave) - self.totalFailed) + ' remaining posts')
        if self.totalFailed > 0:
            print('Error saving files from ' + str(self.totalFailed) + ' remaining posts')

    def saveGfycats(self, urls):
        print('\t' + str(len(urls)) + ' gfycat posts')
        client = GfycatClient()
        numFailed = 0
        for url in urls:
            try:
                urllib.request.urlretrieve(client.query_gfy(url.split('/')[-1])['gfyItem']['mp4Url'], self.dest + '/' + url.split('/')[-1] + '.mp4')
            except:
                numFailed+=1
        if numFailed > 0:
            print('\t\t' + str(numFailed) + ' failed')
        print('\t\t' + str(len(urls) - numFailed) + ' saved')
        self.totalFailed+=numFailed

    def saveImgurAlbums(self, albums):
        print('\t' + str(len(albums)) + ' imgur albums')
        numFailed = 0
        totalImages = 0
        for album in albums:
            imagesFound = []
            r = requests.get('http://imgur.com/a/' + album.split('/')[-1] + '/layout/blog')
            for item in re.findall('.*?{"hash":"([a-zA-Z0-9]+)".*?"ext":"(\.[a-zA-Z0-9]+)".*?', r.content.decode('utf-8')):
                imagesFound.append(item[0] + item[1])
            for image in imagesFound:
                try:
                    urllib.request.urlretrieve('http://i.imgur.com/' + image, self.dest + '/' + image.split('/')[-1])
                except:
                    numFailed+=1
            totalImages+=len(imagesFound)
        print('\t\t' + str(totalImages) + ' pictures from albums')
        if numFailed > 0:
            print('\t\t\t' + str(numFailed) + ' failed')
        print('\t\t\t' + str(totalImages - numFailed) + ' saved')
        self.totalFailed += numFailed

    def tryYouTubeDownload(self, domain, links):
        self.ytdlOptions = {'outtmpl': self.dest + '/%(title)s.%(ext)s', 'quiet': True, 'format': 'best'}
        print('\t' + str(len(links)) + ' ' + domain + ' links')
        numFailed = 0
        for link in links:
            try:
                with youtube_dl.YoutubeDL(self.ytdlOptions) as ydl:
                    ydl.download([link])
            except:
                numFailed+=1
        if numFailed == len(links):
            print('\t\tUnknown domain - see https://github.com/codsane/snooge/blob/master/README.md for instructions to add parser')
        else:
            if numFailed > 0:
                print('\t\t' + str(numFailed) + ' failed')
            print('\t\t' + str(len(links) - numFailed) + ' saved')

    def alreadySaved(self, postID):
        savedFile = open('saved.txt', 'r')
        alreadyPosted = savedFile.read().split(',')
        return postID in alreadyPosted

    def addToSaved(self, postID):
        with open('saved.txt', 'a') as appendFile:
            appendFile.write(postID + ',')


snooge = Snooge()
snooge.grab()
snooge.save()