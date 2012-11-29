#!/usr/bin/env python
__title__="PICASA SYNC"
gap=int(len(__title__))
spacer=60
__description__="""

%s %s %s
A script to sync picasa web albums with a local dir

Requires googlecl

%s
""" % (spacer/2*"*",__title__,spacer/2*"*",(spacer+gap+2)*"*")

import subprocess
import csv
import StringIO
import logging
import os, sys
import argparse
from argparse import RawTextHelpFormatter
from urlparse import urlsplit
import urllib2

logger = logging.getLogger('picasa-backup')

logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

photos_path = os.path.join('/media/data/photos')


def get_albums():
    cmd = ['google', 'picasa','list-albums']
    cmds = " ".join(cmd)
    logger.debug('Running: %(cmds)s' % locals())
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)


    out,err = p.communicate()

    f = StringIO.StringIO(out)
    reader =csv.reader(f)

    albums={}
    for row in reader:
        albums[row[0]]={'name':row[0],'url':row[1]}

    return albums

def create_album(album):

    cmd = ['google', 'picasa','create','%(album)s' % locals()]
    cmds = " ".join(cmd)
    logger.debug('Running: %(cmds)s' % locals())
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    out,err=p.communicate()

    if len(err)>0:
        return True
    else:
        print err
        return False
        
def url2name(url):
    return os.path.basename(urlsplit(url)[2])

def download(url, localFileName = None):
    localName = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if r.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url: 
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(r.url)
    if localFileName: 
        # we can force to save the file as specified name
        localName = localFileName
    f = open(localName, 'wb')
    f.write(r.read())
    f.close()

def upload_photo(album,photo):


    cmd = ['google', 'picasa','post','--title=%(album)s' % locals(),'--src=%(photo)s' % locals()]
    cmds = " ".join(cmd)
    logger.debug('Running: %(cmds)s' % locals())
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    out,err=p.communicate()

    if len(err)>0:
        return True
    else:
        print err
        return False



def get_photos(album):

    cmd = ['google', 'picasa','list','--title=%(album)s' % locals()]
    cmds = " ".join(cmd)
    logger.debug('Running: %(cmds)s' % locals())
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    out,err = p.communicate()

    f = StringIO.StringIO(out)
    reader =csv.reader(f)

    photos={}
    for row in reader:
        fileName, fileExtension = os.path.splitext(row[0])
        photos[fileName]={'name':fileName,'url':row[1],'extension':fileExtension,'synced':False}

    return photos


def main(argv=None):

    global r

    if argv is None:
        argv = sys.argv


    parser = argparse.ArgumentParser(
       description=__description__,formatter_class=RawTextHelpFormatter)

    parser.add_argument('photos_path',help="path to local photos")

    try:
        args = parser.parse_args()
    except:
        sys.exit(1)

    photos_path = args.photos_path

    albums={}
    albums=get_albums()

    logger.info("Found %d existing albums" % len(albums))


    for dirname, dirnames, filenames in os.walk(photos_path):
        for subdirname in dirnames:
            if subdirname in albums:
                logger.info('%(subdirname)s album exists!' % locals())
                photos=get_photos(subdirname)
                num_photos=len(photos)
                logger.info('%(subdirname)s: %(num_photos)d existing photos' % locals())
            else:
                photos={}
                num_photos=len(photos)
                logger.debug('%(subdirname)s album does not exist' % locals())
                if create_album(subdirname):
                    logger.info('Created album %(subdirname)s' % locals())
                else:
                    logger.warning('Could not create %(subdirname)s' % locals())
                    continue

            for dirname2, dirnames2, filenames in os.walk(os.path.join(dirname,subdirname)):
                num_files=len(filenames)

                if num_files != num_photos:
                    logger.warning('%(subdirname)s: local Files %(num_files)d, Web Photos: %(num_photos)s' % locals())
                for f in filenames:
                    filename, fileExtension = os.path.splitext(f)
                    filename=filename.replace(',',' ')
                    if filename in photos:
                        photos[filename]['synced']=True
                        logger.debug('%(subdirname)s: %(filename)s exists, skipping' % locals())
                    else:
                        logger.debug('%(subdirname)s: %(filename)s does not exist' % locals())
                        photos[filename] = {}
                        if upload_photo(subdirname,os.path.join(dirname,subdirname,f)):
                            logger.info('%(subdirname)s: Uploaded %(filename)s' % locals())
                        
                            photos[filename]['synced']=True
                        else:

                            photos[filename]['synced']=False
                            logger.warning('%(subdirname)s: Failed to upload %(filename)s' % locals())

            for k,p in photos.iteritems():
                if not p['synced'] and p['url']:
                    download(p['url'],os.path.join(dirname,subdirname,p['name']+"."+p['extension'])
                    logger.info('%(subdirname)s: Downloading %(k)s' % locals())

if __name__ == "__main__":


    sys.exit(main())
