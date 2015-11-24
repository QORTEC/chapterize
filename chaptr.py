#!/usr/bin/python
# Chapterize
# version 0.25
#
# To run this application you need ffmpeg and rainbowcrack (with a custom algorithm library)
# FFmpeg: 2.8.2 -- https://www.ffmpeg.org/
# RainbowCrack: 1.6.1 -- http://project-rainbowcrack.com
# RainbowCrack custom algorithm
#   File: alglib1.cpp -- https://ffmpeg.org/pipermail/ffmpeg-devel/2015-July/175489.html
#   Build Instructions:  http://project-rainbowcrack.com/alglib.htm
#
# Generate Rainbowtable: (using custom algorithm)
#./rtgen audible byte 4 4 0 10000 10008356 0
#./rtgen audible byte 4 4 1 10000 10008356 0
#./rtgen audible byte 4 4 2 10000 10008356 0
#./rtgen audible byte 4 4 3 10000 10008356 0
#./rtgen audible byte 4 4 4 10000 10008356 0
#./rtgen audible byte 4 4 5 10000 10008356 0
#./rtgen audible byte 4 4 6 10000 10008356 0
#./rtgen audible byte 4 4 7 10000 10008356 0
#./rtgen audible byte 4 4 8 10000 10008356 0
#./rtgen audible byte 4 4 9 10000 10008356 0
#./rtsort *.rt
#
# Move Rainbowtable
#   1. go to the rainbowcrack directory & create a new folder called activation_bytes
#   2. place all the .rt files into the activation_bytes folder
#   3. backup (zip?) activation_bytes folder in case you need a copy in the future...
#      you really don't want to regenerate the rainbow table, how long did it take?
#
# Your ready to run chaptr (Chapterize)
#
# NOTE:
#   For manual setup make sure that applications are properly linked below
#
# Import needed modules
import os
import sys
import argparse
import re
import glob
import time
import subprocess

# Multi-Threading/Processing
import Queue
import threading
import multiprocessing

from os.path import expanduser
home = expanduser("~")

# NOTE: user local applications
rcrack  = home+"/.apps/rainbowcrack/rcrack"
rcrackd = home+"/.apps/rainbowcrack"
ffmpeg  = home+"/.apps/ffmpeg/ffmpeg"
ffprobe = home+"/.apps/ffmpeg/ffprobe"

#ext_list   = []
input_list = [] # currently sys.argv
file_list  = [] # list of valid targets
file_dic   = {} # dictionary of information for valid targets
file_path  = None # string; file path of current job
hash_byte  = {} # dictionary of checksums and activation_bytes

threads = multiprocessing.cpu_count()
file_information_queue = Queue.Queue()
file_convert_queue  = Queue.Queue()
file_activate_queue = Queue.Queue()
start = time.time()

# crash if applications are missing
for file_path in (rcrack, ffmpeg, ffprobe):
    if not os.path.isfile(file_path):
        print "application missing", file_path
        exit()

# parse terminal arguments
parser = argparse.ArgumentParser(description='Chapterize: Audio Book Converter')
parser.add_argument('-o', '--output',
    nargs=1,
    help='path to output directory'
)
parser.add_argument('-y',
    action="store_true",
    help='overwrite existing files'
)
parser.add_argument('-f',
    action='append',
    choices=['mp3', 'mp4', 'm4a', 'm4b'],
    help="output file format"
)
parser.add_argument('-activation_bytes',
    nargs=2,
    help="define [Checksum] [Byte]"
)
parser.add_argument('input',
    nargs='*',
    help="directories and or files to convert"
)
parser.add_argument('-v',
    action="store_true",
    help='about'
)
if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args=parser.parse_args()

# about information
if args.v is True:
    print u'Chapterize\n\
    Version:\t0.25\n\
    Github:\thttps://github.com/QORTEC/chapterize\n\
\n\
Special Thanks:\n\
    K\u0101L\u0113\t for the application name\n\
    Popey\tfor his great suggestions\n\
    DareDevlen\tfor helping me debugg code'
    exit()

input_list = args.input
overwrite = args.y

# extension list
ext_list = args.f
if ext_list is None:
    ext_list = ['m4b', 'mp3']

if args.activation_bytes is not None:
    hash_byte[args.activation_bytes[0]] = args.activation_bytes[1]

# run each app input separately
for file_path in args.input:
    # if input is supported file add to list
    if os.path.isfile(file_path):
        extensions = ('.mp4','.m4a','.m4b','.aax')
        if file_path.lower().endswith(extensions):
            file_list.append(file_path)
    # if input is directory get list of supported files then add to list
    if os.path.isdir(file_path):
        extensions = ('*.mp4','*.m4a','*.m4b','*.aax',)
        for extension in extensions:
            file_list.extend(glob.glob(file_path+"/"+extension))

# threads!!!
class file_information(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        while True:
            # grabs file_path form queue
            file_path = self.queue.get()
            
            # get ffprobe output
            ffprobe_output = subprocess.Popen([ffprobe, file_path],  stderr=subprocess.PIPE).stderr.read()
                
            try:
                # get checksum form ffprobe
                checksum = re.search(r'checksum[A-Za-z0-9= ]+', ffprobe_output).group()
                checksum = re.sub(r'checksum[= ]+','', checksum)
                
                if checksum not in hash_byte:
                    hash_byte[checksum] = None
                    print 'New checksum found:', checksum
            except:
                checksum = None
            try:
                # audio information
                audio_info = ffprobe_output
                audio_info = re.sub(r'Duration:[^;]+', '', audio_info)
                audio_info = re.sub(r'[^;]+Metadata:', '', audio_info)
                
                title = re.search(r'title [^\n]*', audio_info).group()
                title = re.sub(r'title [ ]+: ', '', title)
                
                genre = re.search(r'genre [^\n]*', audio_info).group()
                genre = re.sub(r'genre [ ]+: ', '', genre)
                
                artist = re.search(r'artist [^\n]*', audio_info).group()
                artist = re.sub(r'artist [ ]+: ', '', artist)
                
                album_artist = re.search(r'album_artist [^\n]*', audio_info).group()
                album_artist = re.sub(r'album_artist [ ]+: ', '', album_artist)
                
                album = re.search(r'album [^\n]*', audio_info).group()
                album = re.sub(r'album [ ]+: ', '', album)
                
                comment = re.search(r'comment [^\n]*', audio_info).group()
                comment = re.sub(r'comment [ ]+: ', '', comment)
                
                copyright = re.search(r'copyright [^\n]*', audio_info).group()
                copyright = re.sub(r'copyright [ ]+: ', '', copyright)
                
                date = re.search(r'date [^\n]*', audio_info).group()
                date = re.sub(r'date [ ]+: ', '', date)
                
                file_dic[file_path] = {
                    'title' : { title : None },
                    'album' : { album : None },
                    'artist' : { artist : None },
                    'album_artist' : { album_artist : None },
                    'copyright' : { copyright : None },
                    'comment' : { comment : None },
                    'genre' : { genre : None },
                    'date' : { date : None },
                    'performer' : { None : None },
                    'composer' : { None : None },
                    'publisher' : { None : None },
                    'disc' : { None : None },
                    'track' : { None : None },
                    'lyrics' : { None : None },
                    'language' : { None : None },
                    'encoder' : { None : None },
                    'encoded_by' : { None : None },
                    'checksum' : checksum,
                    'chapter' : []
                }
                
                track_info = ffprobe_output
                track_info = re.findall(r'Chapter.*?title[^\n]*', track_info, re.S)
                for match in track_info:
                    title  = re.sub(r'[^;]+ title [ ]+: ', '', match)
                    start = re.findall(r'start (.*?),', match)
                    end   = re.findall(r'end (.*?)\n',  match)
                    file_dic[file_path]['chapter'].append({'title' : title, 'start' : start, 'end' : end})
            except:
                pass
            
            #signals to queue job is done
            self.queue.task_done()

class file_convert(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        while True:
            file_path = self.queue.get()
            
            def file_info(input_var):
                try:
                    if file_dic[file_path][input_var].keys() is not None:
                        value = file_dic[file_path][input_var].keys()[0]
                        return value
                    
                    if file_dic[file_path][input_var].value() is not None:
                        value = file_dic[file_path][input_var].values()[0]
                        return value
                
                except:
                    pass
                
                return ''
            
            def meta_info(input_var):
                try:
                    value = file_info(input_var)
                    return '-metadata '+input_var+'="'+value+'" '
                except:
                    pass
                
                return ''
            
            def convert(file_path, extension, title='', start='', end=''):
                checksum = file_dic[file_path]['checksum']
                directory_path = os.path.dirname(file_path)+'/' ## directory of file
                file_name = file_info('title')
                file_output = '"'+directory_path+file_name+'.'+extension+'"'
                file_path   = '"'+file_path+'"'
                
                if start:
                    start = ' -ss '+start+' '
                if end:
                    end   = ' -to '+end+' '
                
                if checksum:
                    activate = ' -activation_bytes '+hash_byte[checksum]+' '
                if not checksum:
                    activate = ''
                
                if not title:
                    meta_title = meta_info('title')
                if title:
                    meta_title = ' -metadata title="'+file_name+' - '+title+'" '
                
                if overwrite is True:
                     write = ' -y '
                if overwrite is False:
                     write = ' -n '
                
                variable = start+end+write+' -vn '
                metadata = (
                    meta_title
                    +meta_info('album')
                    +meta_info('artist')
                    +meta_info('album_artist')
                    +meta_info('copyright')
                    +meta_info('comment')
                    +meta_info('genre')
                    +meta_info('date')
                    +meta_info('performer')
                    +meta_info('composer')
                    +meta_info('publisher')
                    +meta_info('disc')
                    +meta_info('track')
                    +meta_info('lyrics')
                    +meta_info('language')
                    +meta_info('encoder')
                    +meta_info('encoded_by')
                )
                
                #ffmpeg+' -loglevel panic '+activate+' -i '+file_path+variable+metadata+file_output
                
                #subprocess.Popen(['echo '+ffmpeg+' -loglevel panic '+activate+' -i '+file_path+variable+metadata+file_output], shell=True).wait()
                #print 'echo '+ffmpeg+' -loglevel panic '+activate+' -i '+file_path+variable+metadata+file_output
                
                #print ffmpeg
                #print activate
                #print file_path
                #print variable
                #print metadata
                #print file_output
                
                # Title:
                # {Name} {Track No} - {Title}
                # {directory path}/{Name}/{Output File Name}
                # directory should be same as source file...
                
                if extension in ('mp4','m4a','m4b'):
                    #print 'debut running '+extension
                    variable = variable+' -c:a copy -f mp4 '
                    subprocess.Popen([ffmpeg+' -loglevel panic '+activate+' -i '+file_path+variable+metadata+file_output], shell=True).wait()
                
                if extension is 'mp3':
                    #print 'debut running '+extension
                    variable = variable+' -write_xing 0 '
                    directory_path  = directory_path+file_name+'/'
                    file_output = '"'+directory_path+file_name+' - '+title+'.'+extension+'"'
                    subprocess.Popen([ffmpeg+' -loglevel panic '+activate+' -i '+file_path+variable+metadata+file_output], shell=True).wait()
            
            for extension in ext_list:
                if (extension in ('mp4','m4a','m4b') and
                    not file_path.lower().endswith(('.mp4','.m4a','m4b'))):
                    convert(file_path, extension)
                    #pass
                
                if (extension in ('mp3') and
                    not file_path.lower().endswith('.mp3')):
                    for chaptr in file_dic[file_path]['chapter']:
                        start = chaptr['start'][0]
                        end   = chaptr['end'][0]
                        title = chaptr['title']
                        
                        directory = os.path.dirname(file_path)+"/"
                        directory = directory+file_info('title')
                        
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        
                        convert(file_path, extension, title, start, end)
            
            #signals to queue job is done
            self.queue.task_done()

class file_activate(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        while True:
            file_path = self.queue.get()
            checksum  = file_dic[file_path]['checksum']
            
            # get activation_bytes to extract audio
            for checksum, byte in hash_byte.iteritems():
                # if activation_bytes are unknown look them up
                if byte == None:
                    rcrack_output = subprocess.Popen([rcrack+' '+rcrackd+'/activation_bytes/*.rt -h '+checksum], shell=True, cwd=rcrackd, stdout=subprocess.PIPE).stdout.read()
                    
                    byte = re.search(r'hex:[A-Za-z0-9]+', rcrack_output).group()
                    byte = re.sub(r'hex:','', byte)
                    
                    hash_byte[checksum] = byte
                    print hash_byte
            
            #signals to queue job is done
            self.queue.task_done()

def main():
    #spawn a pool of threads, and pass them queue instance
    for i in range(threads-1):
        t = file_information(file_information_queue)
        t.setDaemon(True)
        t.start()
    
    #populate queue with data
    for file_path in file_list:
        file_information_queue.put(file_path)
    
    #wait on the queue until everything has been processed
    file_information_queue.join()
    
    for i in range(1):
        t = file_activate(file_activate_queue)
        t.setDaemon(True)
        t.start()
    
    for file_path in file_list:
        file_activate_queue.put(file_path)
        #pass
    
    #GUI...
    
    file_activate_queue.join()
    
    for i in range(threads-1):
        t = file_convert(file_convert_queue)
        t.setDaemon(True)
        t.start()
    
    for file_path in file_list:
        file_convert_queue.put(file_path)
        #pass
        
    #wait on the queue until everything has been processed
    file_convert_queue.join()
    
main()
print "Elapsed Time: %s" % (time.time() - start)

#for file_path in file_list:
#    print file_path
