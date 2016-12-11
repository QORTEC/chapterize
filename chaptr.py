#!/usr/bin/python
__version__ = '0.3'

# Import needed modules
import os
import sys
#import argparse
import re
import glob
import json
import subprocess
import ffmpy
import logging
import time
import multiprocessing
#import pprint



# Script Start
start_time = time.time()

# get user home directory
home = os.path.expanduser("~")

# set default location for local apps
rcrackd = home+"/.apps/rainbowcrack"
ffmpegd = home+"/.apps/ffmpeg"

# list the supported file extensions
chapter = ('.mp3',)                 #ouput individual files for each chapter
volume  = ('.mp4','.m4a','.m4b',)   #ouput a single file with chapter markers
supported = volume+('.aax',)        #supported input file types



class info(object):
    """retreave information needed for file conversion"""
    def __init__(self, file=None):
        self.file = file
        self.file_dic  = {}
        
    
    def ffprobe(self):
        """use FFprobe we retreave metadata used to create/convert the new audio files"""
        ffprobe_output = ffmpy.FFprobe(
            global_options='-hide_banner',
            inputs={self.file : '-print_format json -show_format -show_chapters -show_streams'}
        ).run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        
        ffprobe_output = list(ffprobe_output)
        ffprobe_output[0] = ffprobe_output[0].decode('utf-8')
        ffprobe_output[1] = ffprobe_output[1].decode('utf-8')
        ffprobe_output[0] = json.loads(ffprobe_output[0])
        
        try:
            checksum = re.search(r'checksum[A-Za-z0-9= ]+', ffprobe_output[1]).group()
            checksum = re.sub(r'checksum[= ]+','', checksum)
        except:
            checksum = None
        
        file_path     = ffprobe_output[0]['format']['filename']
        title         = ffprobe_output[0]['format']['tags']['title']
        album         = ffprobe_output[0]['format']['tags']['album']
        artist        = ffprobe_output[0]['format']['tags']['artist']
        album_artist  = ffprobe_output[0]['format']['tags']['album_artist']
        copyright     = ffprobe_output[0]['format']['tags']['copyright']
        comment       = ffprobe_output[0]['format']['tags']['comment']
        genre         = ffprobe_output[0]['format']['tags']['genre']
        date          = ffprobe_output[0]['format']['tags']['date']
        checksum      = checksum
        
        self.file_dic[self.file] = {
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
        
        # mp3 chpater seperation code...
        track = [ 0 , len(ffprobe_output[0]['chapters']) ]
        for chapter in ffprobe_output[0]['chapters']:
            title = chapter['tags']['title']
            start = chapter['start_time']
            end   = chapter['end_time']
            track[0] += 1
            
            self.file_dic[self.file]['chapter'].append({
                'title' : { title : None },
                'start' : start,
                'end' : end,
                'track' : { str(track[0])+'/'+str(track[1]) : None }
            })
        
        return self.file_dic
    
    
    def rcrack(self, checksum=None):
        """using rcrack we retreave "actavation bytes" needed to decrypt certain audio files"""
        cmd  = ['./rcrack']
        cmd += ['./activation_bytes/*.rt']
        cmd += [['-h '+checksum]]
        cmdS = subprocess.list2cmdline(cmd)
        
        #print(cmdS)
        byte = subprocess.Popen(cmdS, shell=True, cwd=rcrackd, stdout=subprocess.PIPE).stdout.read()
        byte = byte.decode('utf-8', 'ignore')
        
        byte = re.search(r'hex:[A-Za-z0-9]+', byte).group()
        byte = re.sub(r'hex:','', byte)
        
        return byte


class convert(object):
    """create/convert the audio files..."""
    def __init__(self, file_dic=None, hash_byte=None):
        self.file_dic = file_dic
        self.file = list(file_dic)[0]
        
        self.extension = []
    
    
    def argument(self, dictionary, element, value=False):
        """check for a overide valude for the dictionary entry, and return the FFmpeg metadata command or the falue its self"""
        try:
            if list(dictionary[element].keys())[0] is not None:
                output = list(dictionary[element].keys())[0]
            
            if list(dictionary[element].values())[0] is not None:
                output = list(dictionary[element].values())[0]
            
            if value is True:
                return output
            else:
                return '-metadata %s="%s"' % (element, output)
        
        except:
            pass
        
        return ''
    
    
    def command(self, extension=None, overwrite=False):
        """using metadata create a list of commands to create/convert the new audio files..."""
        chapter = ('.mp3')
        volume  = ('.mp4','.m4a','.m4b')
        
        
        extension = '.mp3'
        overwrite = False
        
        
        if overwrite is True:
             cmd_write = ['-y']
        else:
             cmd_write = ['-n']
        
        cmd_global_common = ['-loglevel panic'] + cmd_write
        
        checksum = self.file_dic[self.file]['checksum']
        if checksum:
            cmd_activate = ['-activation_bytes %s' % hash_byte[checksum]]
        if not checksum:
            cmd_activate = ['']
        #cmd_activate = ['']
        
        
        cmd_metadata_common  = [self.argument(self.file_dic[self.file], 'album')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'artist')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'album_artist')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'copyright')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'comment')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'genre')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'date')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'performer')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'composer')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'publisher')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'disc')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'lyrics')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'language')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'encoder')]
        cmd_metadata_common += [self.argument(self.file_dic[self.file], 'encoded_by')]
        
        
        cmd_return = []
        
        if extension in volume:
            #['-metadata major_brand="M4B"', '-metadata compatible_brands="M4A mp42isom"']
            cmd_metadata  = [] + cmd_metadata_common
            cmd_metadata += [self.argument(self.file_dic[self.file], 'title')]
            cmd_metadata += [self.argument(self.file_dic[self.file], 'track')]
            
            cmd_global = [] + cmd_global_common
            cmd_input  = [] + cmd_activate
            cmd_output = [] + ['-vn', '-c:a copy'] + cmd_metadata + ['-f mp4']
            
            cmd_global = list(filter(None, cmd_global))
            cmd_input  = list(filter(None, cmd_input))
            cmd_output = list(filter(None, cmd_output))
            
            cmd_global = ' '.join(cmd_global)
            cmd_input  = ' '.join(cmd_input)
            cmd_output = ' '.join(cmd_output)
            
            file_name  = '%s.m4b' % self.argument(self.file_dic[self.file], 'album', value=True)
            
            
            cmd_return += [[[cmd_global], [self.file], [cmd_input], [file_name], [cmd_output]]]
        
        if extension in chapter:
            
            cmd_global = [] + cmd_global_common
            cmd_input  = [] + cmd_activate
            cmd_output = [] + ['-an', '-vcodec copy']
            
            file_name = '%s.jpg' % self.argument(self.file_dic[self.file], 'album', value=True)
            
            cmd_global = list(filter(None, cmd_global))
            cmd_input  = list(filter(None, cmd_input))
            cmd_output = list(filter(None, cmd_output))
            
            cmd_global = ' '.join(cmd_global)
            cmd_input  = ' '.join(cmd_input)
            cmd_output = ' '.join(cmd_output)
            
            
            cmd_return += [[[cmd_global], [self.file], [cmd_input], [file_name], [cmd_output]]]
            
            
            for chapter in self.file_dic[self.file]['chapter']:
                cmd_metadata  = ['-map_metadata -1', '-map_chapters -1'] + cmd_metadata_common
                cmd_metadata += [self.argument(chapter, 'title')]
                cmd_metadata += [self.argument(chapter, 'track')]
                
                cmd_time   = ['-ss %s' % chapter['start']]
                cmd_time  += ['-to %s' % chapter['end']]
                
                cmd_global = [] + cmd_global_common
                cmd_input  = [] + cmd_activate
                cmd_output = [] + cmd_time + ['-vn', '-write_xing 0'] + cmd_metadata
                
                cmd_global = list(filter(None, cmd_global))
                cmd_input  = list(filter(None, cmd_input))
                cmd_output = list(filter(None, cmd_output))
                
                cmd_global = ' '.join(cmd_global)
                cmd_input  = ' '.join(cmd_input)
                cmd_output = ' '.join(cmd_output)
                
                file_name = '%s - %s.mp3' % (self.argument(self.file_dic[self.file], 'album', value=True), self.argument(chapter, 'title', value=True))
                
                
                cmd_return += [[[cmd_global], [self.file], [cmd_input], [file_name], [cmd_output]]]
        
        return cmd_return
    
    
    def run(self, cmd):
        """convert the audio files..."""
        ffmpy.FFmpeg(
            global_options=cmd[0],
            inputs= { cmd[1] : cmd[2] },
            outputs={ cmd[3] : cmd[4] },
        ).run()


class input(object):
    def __init__(self, input):
        self.file_list = []
        # run each app input separately
        for file_path in input:
            self.file_list += self.validate(file_path)
    
    
    def validate(self, file_path):
        output = []
        
        if os.path.isfile(file_path):
            if file_path.lower().endswith(supported):
                output = [file_path]
        
        if os.path.isdir(file_path):
            for extension in supported:
                output = glob.glob(file_path+"/*"+extension)
        
        return output
    
    
    def list(self):
        return self.file_list


class process(object):
    def __init__(self, process_id, seppuku=False, queue=None):
        self.process_id = process_id
        self.seppuku = seppuku
        self.queue = queue
    
    def is_alive(self):
        is_alive = []
        
        for child_process in self.process_id:
            if child_process.is_alive():
                is_alive += [child_process]
            
        return is_alive
    
    def start(self):
        for child_process in self.process_id:
            child_process.start()
            logging.debug('started child process %s' % child_process)
            
            if self.seppuku:
                self.queue.put('seppuku')
    
    def join(self, join_timeout=None):
        for child_process in self.process_id:
            child_process.join(join_timeout)



# function for Main Script
def queue_list(comment=None):
    # list the number if items in the queue
    print (' ')
    if comment is not None:
        print(comment)
    
    print('ckecksum %s' % q_checksum.qsize())
    print('input    %s' % q_file_list.qsize())
    print('list     %s' % q_file_dic.qsize())
    print('cmd      %s' % q_file_cmd.qsize())
    
    try:
        print('output   %s' % output_queue.qsize())
    except:
        print('output   %s' % q_output.qsize())


def q2q(target=None):
    # this function retreaves items form the output queue and moves them into the proper queue for later use
    
    # Move q_output to q_file_dic
    if target is 'q_file_dic':
        sums = []
        
        while not q_output.empty():
            output = q_output.get()
            
            logging.debug('queue size: %s' % q_output.qsize())
            logging.debug(output)
            
            q_file_dic.put(output)
            
            file_name = list(output)[0]
            checksum = output[file_name]['checksum']
            
            if checksum and checksum not in sums:
                logging.info('Found newe checksum: %s' % checksum)
                q_checksum.put(checksum)
                
                sums += [checksum]
    
    # Move q_output to q_file_cmd
    if target is 'q_file_cmd':
        while not q_output.empty():
            output = q_output.get()
            
            logging.debug('queue size: %s' % q_output.qsize())
            logging.debug(output)
            
            for item in output:
                logging.debug(item)
                logging.debug('cmd_global: %s' % item[0])
                logging.debug('input_file: %s' % item[1])
                logging.debug('cmd_input:  %s' % item[2])
                logging.debug('file_name:  %s' % item[3])
                logging.debug('cmd_output: %s' % item[4])
                
                q_file_cmd.put(item)



# child_process
def proc0(working_queue, dic = {}):
    while True:
        item = working_queue.get()
        
        if item == 'seppuku':
            break
        
        # check if checksum is in local dictionary
        if item and item not in dic:
            logging.info('Found newe checksum: %s' % item)
            dic[item] = None
        
        # lookup infomation in dictionary
        for item, output in dic.items(): #iteritems
            if output == None:
                dic[item] = info().rcrack(item)
            
            #print(dic[item])


def proc1(working_queue, output_queue):
    while True:
        item = working_queue.get()
        
        if item == 'seppuku':
            break
        
        output = info(item).ffprobe()
        output_queue.put(output)
    
    #queue_list()
    #output_queue.cancel_join_thread()


def proc2(working_queue, output_queue, dic):
    while q_file_dic.qsize() > 0:
        try:
            item = working_queue.get(True, 0.8)
        
        except:
            break
        
        output = convert(item, dic).command()
        output_queue.put(output)
    
    #queue_list()
    #output_queue.cancel_join_thread()


def proc3(working_queue):
    while q_file_cmd.qsize() > 0:
        try:
            item = working_queue.get(True, 0.8)
        
        except:
            break
        
        #print(item)



# Main Script
if __name__ == '__main__':
    logging.info('chaptr.py started')
    cpu_core = multiprocessing.cpu_count()
    #cpu_core = 2
    
    queue_info_input  = multiprocessing.Queue()
    queue_info_output = multiprocessing.Queue()
    
    q_size      = 0
    q_output    = multiprocessing.Queue()
    q_file_list = multiprocessing.Queue()
    q_file_dic  = multiprocessing.Queue()
    q_file_cmd  = multiprocessing.Queue()
    q_checksum  = multiprocessing.Queue()
    hash_byte   = multiprocessing.Manager().dict()
    
    join_timeout = 0.2
    
    logging.info('building a list of valid files')
    for blah in input(['test.aax', 'test2.aax', 'test/', '/home/qortec/Desktop/Audible/AAX']).list():
        q_file_list.put(blah)
        q_size += 1
    
    
    
    process_0 = [multiprocessing.Process(target=proc0, args=(q_checksum,  hash_byte)) for i in range(1)]
    process_1 = [multiprocessing.Process(target=proc1, args=(q_file_list, q_output,)) for i in range(cpu_core - 1)]
    process_2 = [multiprocessing.Process(target=proc2, args=(q_file_dic,  q_output, hash_byte,)) for i in range(cpu_core - 1)]
    process_3 = [multiprocessing.Process(target=proc3, args=(q_file_cmd,)) for i in range(cpu_core - 1)]
    
    
    # Step 0.5
    # -- start a single child_process
    # -- use any avaiable method to get the activation bytes
    process(process_0).start()
    
    
    # Step 1:
    # -- start cpu_core - 1 child_process
    # -- use FFprobe to get revelant information form supported files
    process(process_1, True, q_file_list).start()
    
    # -- while child_process are active run
    while process(process_1).is_alive():
        # -- take information form output queue amd move it to the correct queue for later use
        q2q('q_file_dic')
        
        # -- if the output queue is empty try "joining" the process
        if q_output.empty():
            process(process_0).join(join_timeout)
    
    # -- rerun command to clean up any items left in the queue
    q2q('q_file_dic')
    
    
    # Step 1.5
    # -- send seppuku signle
    # -- try "joining" process
    q_checksum.put('seppuku')
    
    # -- while child_process is active run
    while process(process_0).is_alive():
        process(process_0).join(join_timeout)
    
    
    # Step 2:
    # -- start cpu_core - 1 child_process
    # -- use the information provided by FFprobe to create FFmpeg conversion commands
    process(process_2).start()
    
    # -- while child_process are active run
    while process(process_2).is_alive():
        q2q('q_file_cmd')
        
        # -- if the output queue is empty try "joining" the process
        if q_output.empty():
            process(process_2).join(join_timeout)
    
    # -- rerun command to clean up any items left in the queue
    q2q('q_file_cmd')
    
    
    # Step 3:
    # -- start cpu_core - 1 child_process
    # -- run FFmpeg commands to convert audio files...
    process(process_3).start()
    
    # -- while child_process are active run
    while process(process_3).is_alive():
        
        
        # -- if command queue is empty try "joining" the process
        if q_file_cmd.empty():
            process(process_3).join(join_timeout)
    
    
    # Step 4:
    # -- print the run time of app
    # -- we are done!
    print("--- %s seconds ---" % (time.time() - start_time))
    
    
    #if multiprocessing.active_children():
    #    print(multiprocessing.active_children())
    
    sys.exit()
