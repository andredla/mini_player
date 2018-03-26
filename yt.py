#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

# (c) Christopher Down 2011
# See the COPYING file for copyright information.

""" Prints direct URLs to YouTube media. """

from urllib import urlopen
from urlparse import parse_qs
from os.path import basename
import sys

__author__ = 'Christopher Down'
__copyright__ = 'Copyright 2011 %s' % __author__
__license__ = 'BSD'
__version__ = 1.01

class YTURL():
    def __init__(self):
        self.youtubeQueryURL = 'http://youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en'
        self.videoURLListKey = 'url_encoded_fmt_stream_map'
        self.videoIDKeys = [ 'v', 'video_id' ]
        #self.videoItagQualityOrder = [ 38, 37, 22, 45, 44, 35, 18, 34, 43, 5, 17 ]
        self.videoItagQualityOrder = [ 35, 44, 22, 45, 18, 43 ]
        self.allowedVideoIDCharacters = '-_abcdefghijklmnopqrstuvwxyz0123456789'

    def getVideoItags(self, videoID):
        """ Returns the available itags and their associated URLs as a list. """
        availableFormats = {}
        parsedResponse = parse_qs(urlopen(self.youtubeQueryURL % videoID).read())
        if self.videoURLListKey in parsedResponse:
            for videoFormat in parsedResponse[self.videoURLListKey][0].split(','):
                videoFormat = parse_qs(videoFormat)
                if 'url' in videoFormat and 'itag' in videoFormat:
                    availableFormats[int(videoFormat['itag'][0])] = videoFormat['url'][0]
                else:
                    return False
        else:
            return False
        return availableFormats

    def checkIsValidItag(self, itag):
        """ Checks that all arguments are known itags. """
        if itag not in self.videoItagQualityOrder:
            return False
        else:
            return True

    def getPreferredItagOrder(self, preferredItags):
        """ Determines and returns the preferred video itag sorting.
            If argv has a length of 3, this returns a tuple, otherwise, it
            returns a list. """

        if len(preferredItags) == 1:
            v = self.videoItagQualityOrder
            return zip(*sorted(enumerate(v),key=lambda (i,x):abs(v.index(preferredItags[0])-i)))[1]
        elif len(preferredItags) > 1:
            for itag in preferredItags:
                self.videoItagQualityOrder.remove(itag)
            return preferredItags + self.videoItagQualityOrder
        else:
            return self.videoItagQualityOrder

    def checkIsValidVideoID(self, videoID):
        """ Checks that a video ID is syntactically valid. """
        if len(videoID) != 11:
            return False

        for c in videoID:
            if c.lower() not in self.allowedVideoIDCharacters:
                return False
        return True

    def stripYouTubeURL(self, url):
        """ Strips a YouTube URL to the video ID. """
        if '?' in url:
            url = url[url.index('?') + 1:]
            urlPost = parse_qs(url)
            for key in self.videoIDKeys:
                if key in urlPost:
                    return urlPost[key][0]

        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]

        if url.startswith('www.'):
            url = url[4:]

        if url.startswith('youtu.be/'):
            return url[9:]
        elif url.startswith('youtube.com/v/'):
            return url[14:]

        return url

def main():
    if len(sys.argv) == 1:
        print >> sys.stderr, 'Usage: %s id [itag ...]' % basename(sys.argv[0])
        sys.exit(1)

    y = YTURL()

    videoID = y.stripYouTubeURL(sys.argv[1])

    if not y.checkIsValidVideoID(videoID):
        print >> sys.stderr, 'Invalid video ID.'
        sys.exit(2)

    for itag in sys.argv[2:]:
        if not itag.isdigit() or not y.checkIsValidItag(int(itag)):
            print >> sys.stderr, '%s is not a valid itag.' % itag
            sys.exit(3)

    preferredItags = map(int, sys.argv[2:])
    availableFormats = y.getVideoItags(videoID)

    if availableFormats is not False:
        for itag in y.getPreferredItagOrder(preferredItags):
            if itag in availableFormats:
                print availableFormats[itag]
                sys.exit(itag)
    else:
        print >> sys.stderr, """ The YouTube API returned data from which no
                                 media URL could be retrieved. """
        sys.exit(4)

if __name__ == '__main__':
    main()

