# Chapterize
####Audio Book Converter

The primary purpose of Chapterize is to convert Audio Books form one format to another. 

Features
- convert audio book into the mp4 format [.m4a, .m4b]
- convert audio book into the mp3 format
  - each chapter is separated into its own mp3 file [no more seeking around 10hr book!]
- multithreaded for faster batch processing (Note: currently it dedicates one CPU to one input file)
- input multiple files or entire folders for batch processing

Limitations:
- limited support for file formats, officially we only support mp4 [m4a m4b] for input, and we can output to mp4 and mp3.
- terminal only application (you should really learn how to use the terminal)

The application is in early development, if you find any bugs please report them on GitHub or submit a pull request.

## Setup
To run Chapterize you will need RainbowCrack, Custom Algorithm, FFmpeg (with support for -activation_bytes)
- FFmpeg: 2.8.2 -- https://www.ffmpeg.org/
- RainbowCrack: 1.6.1 -- http://project-rainbowcrack.com
- RainbowCrack custom algorithm:
  - File: alglib1.cpp -- https://ffmpeg.org/pipermail/ffmpeg-devel/2015-July/175489.html
  - Build Instructions:  http://project-rainbowcrack.com/alglib.htm

Chapterize expects to find the FFmpeg binaries in ``~/.apps/ffmpeg`` and the RainbowCrack binaries in ``~/.apps/rainbowcrack``

Once your done downloading and setting up FFmpeg and Rainbow crack you will need to build the custom algorithm and place it in the RainbowCrack folder.

Once your done with that you will need to create the rainbow table (command below)
- This process will take a **long** time (may be 10hr+ per table)
- I suggest trying to build the first table and sort it (first and last command) this may be good enough...

**Note**:
- to run RainbowCrack you need to be in the same directory as the binaries
- to run RainbowCrack you need **read** **write** and **execute** permissions on the binaries

````
#!/bin/bash
./rtgen audible byte 4 4 0 10000 10008356 0
./rtgen audible byte 4 4 1 10000 10008356 0
./rtgen audible byte 4 4 2 10000 10008356 0
./rtgen audible byte 4 4 3 10000 10008356 0
./rtgen audible byte 4 4 4 10000 10008356 0
./rtgen audible byte 4 4 5 10000 10008356 0
./rtgen audible byte 4 4 6 10000 10008356 0
./rtgen audible byte 4 4 7 10000 10008356 0
./rtgen audible byte 4 4 8 10000 10008356 0
./rtgen audible byte 4 4 9 10000 10008356 0
./rtsort *.rt
````

Once your done building the tables create a new folder called ````activation_bytes```` place the .rt files in the newly created folder.

At this point you should be setup and to run Chapterize; happy listening.

###Thank You
- KāLē        for the application name
- Popey       for his great suggestions
- DarDevelin  for helping me debug code

----

Donate:
- https://www.paypal.me/QORTEC
- https://www.patreon.com/QORTEC
