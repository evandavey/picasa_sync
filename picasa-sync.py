#!/usr/bin/env python

import subprocess
import csv
import StringIO
import logging
import os
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
		photos[fileName]={'name':fileName,'url':row[1],'extension':fileExtension}

	return photos

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
			if filename in photos:
				logger.debug('%(subdirname)s: %(filename)s exists, skipping' % locals())
			else:
				logger.debug('%(subdirname)s: %(filename)s does not exist' % locals())
				if upload_photo(subdirname,os.path.join(dirname,subdirname,f)):
					logger.info('%(subdirname)s: Uploaded %(filename)s' % locals())
				else:
					logger.warning('%(subdirname)s: Failed to upload %(filename)s' % locals())

