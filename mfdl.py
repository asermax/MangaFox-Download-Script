#!/usr/bin/python
# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-

'''
Mangafox Download Script by Kunal Sarkhel <theninja@bluedevs.net>
Updated by Agustín Carrasco <asermax@gmail.com>
'''

#from IPython.Shell import IPShellEmbed #for debug purposes
#ipshell = IPShellEmbed()

import sys
import re
import os
import urllib
import glob
import shutil
from zipfile import ZipFile
from BeautifulSoup import BeautifulSoup

URL_BASE = "http://mangafox.com/"


def get_page_soup(url):
    """Download a page and return a BeautifulSoup object of the html"""
    urllib.urlretrieve(url, "page.html")
    html = ""
    with open("page.html") as html_file:
        for line in html_file:
            html += line
    return BeautifulSoup(html)
    
def get_volume_chapter_number(url):
    split = url.rsplit("/")
    return '%g' % float(split[-3].replace('v', '')), \
        '%g' % float(split[-2].replace('c', ''))
            
def get_chapter_urls(manga_name):
    """Get the chapter list for a manga"""
    print "Getting chapter urls"
    url = "{0}manga/{1}?no_warning=1".format(URL_BASE, manga_name.lower())
    print "Url: " + url
    
    soup = get_page_soup(url)
    chapters = {}
    links = soup.findAll('a', {"class": "tips"})
    
    for link in links:
        url = link['href'].replace('1.html', '')
        volume, chapter = get_volume_chapter_number(url)
        
        if chapters.has_key(volume):
            chapters[volume][chapter] = url
        else:
            chapters[volume] = {chapter: url}
        
    if(len(links) == 0):
        print "Warning: Manga either unable to be found, or no chapters - please check the url above";       
        
    return chapters
       
def find_volume_chapter(chapters, number):
    matching = []
    
    for volume in chapters:
        matching.extend([(volume, chapter) for chapter in chapters[volume] 
            if chapter == number])
                  
    chapter = (None, None)
      
    if not matching:
        print "Chapter not found"
  
    elif len(matching) > 1:
        print "Warning: more than one chapter with that number, try again using the fully qualified chapter (e.g. v1c1)"
        print 'Chapters found: ',
        
        for chap in matching:
            print 'v%sc%s' % chap,
    
        print
        
    else:
        chapter = matching[0]
                           
    return chapter
    
def strip_volume_chapter(fully_qualified):
    match = re.search('v(\d+)c(\d+)', fully_qualified).groups()
    chapter = (None, None)
    
    if match:
        chapter = match.groups()
    else:
        print "Chapter not found"
    
    return 

def is_number(string):
    try:
        float(string)
        return True
    except:
        return False   
 
def clean_input_chapter(chapters, chapter):
    if is_number(chapter):
        volume, chapter = find_volume_chapter(chapters, chapter)
    else:
        volume, chapter = strip_volume_chapter(chapter)
        
    return volume, chapter

def get_volumes_in_range(chapters, volume_start, volume_end):
    return [volume for volume 
        in sorted(chapters.iteritems(), key=lambda x: float(x[0]))
        if float(volume[0]) >= float(volume_start) 
        and float(volume[0]) <= float(volume_end)]
          
def get_page_numbers(soup):
    """Return the list of page numbers from the parsed page"""
    raw = soup.findAll('select', {'class': 'm'})[0]
    raw_options = raw.findAll('option')
    pages = []
    for html in raw_options:
        pages.append(html['value'])
        
    pages.remove('0')
    return pages

def get_chapter_image_urls(chapter_url):
    """Find all image urls of a chapter and return them"""
    print "Getting chapter urls"
    chapter = get_page_soup(chapter_url)
    pages = get_page_numbers(chapter)
    image_urls = []
    print "Getting image urls..."
    for page in pages:
        print "page: {0}".format(page)
        print "Getting image url from {0}{1}.html".format(chapter_url, page)
        page_soup = get_page_soup(chapter_url + page + ".html")
        images = page_soup.findAll('img', {'id': 'image'})
        image_urls.append(images[0]['src'])
    return image_urls

def check_jpg(jpeg_file):
    data = open(jpeg_file,'rb').read(11)
    return data[:4] == '\xff\xd8\xff\xe0' and data[6:] == 'JFIF\0'

def download_urls(image_urls, manga_name, chapter_number):
    """Download all images from a list"""
    num = 1
    os.makedirs("{0}/{1}/".format(manga_name, chapter_number))
    for url in image_urls:
        while True:
            filename = "./{0}/{1}/{2:03}.jpg".format(manga_name,
                chapter_number, num)
            print "Downloading {0} to {1}".format(url, filename)
            urllib.urlretrieve(url, filename)
        
            if check_jpg(filename):
                num = num + 1
                break
            else:
                print 'Re',

def makecbz(dirname):
    """Create CBZ files for all files in a directory."""
    dirname = os.path.abspath(dirname)
    zipname = dirname + '.cbz'
    images = glob.glob(dirname + "/*.jpg")
    myzip = ZipFile(zipname, 'w')
    for filename in images:
        print("writing {0} to {1}".format(filename, zipname))
        myzip.write(filename)
    myzip.close()

def download_chapter(manga_name, volume, chapter, url):
    name = 'v%sc%s' % (volume, chapter)
    print("===============================================")
    print "Chapter " + name
    print("===============================================")
    image_urls = get_chapter_image_urls(url)
    download_urls(image_urls, manga_name, name)
    download_dir = "./{0}/{1}".format(manga_name, name)
    makecbz(download_dir)
    shutil.rmtree(download_dir)

def download_manga_range(manga_name, range_start, range_end):
    """Download a range of a chapters"""
    volumes = get_chapter_urls(manga_name)
    
    volume_start, chapter_start = clean_input_chapter(volumes, range_start)
    volume_end, chapter_end = clean_input_chapter(volumes, range_end)

    if volume_start and volume_end:     
        for volume, chapters in get_volumes_in_range(volumes, volume_start,
            volume_end):
            for chapter, url in [chapter for chapter 
                in sorted(chapters.iteritems(), key=lambda x: float(x[0]))
                if float(chapter[0]) >= float(chapter_start)
                and float(chapter[0]) <= float(chapter_end)]:
                download_chapter(manga_name, volume, chapter, url)
            
        os.remove("page.html")

def download_manga_volume(manga_name, volume_start, volume_end=None):       
    volumes = get_chapter_urls(manga_name)
    
    if not volume_start.isdigit():
        volume_start = volume_start.replace('v', '')
            
    if not volume_end:
        volume_end = volume_start
    elif not volume_end.isdigit():
        volume_end = volume_end.replace('v', '')
        
    for volume, chapters in get_volumes_in_range(volumes, volume_start,
        volume_end):
        for chapter, url in sorted(chapters.iteritems(),
            key=lambda x: float(x[0])):

            download_chapter(manga_name, volume, chapter, url)   
    
    os.remove("page.html")
    
def download_manga(manga_name, chapter_number=None):
    """Download all chapters of a manga"""
    volumes = get_chapter_urls(manga_name)
    
    if chapter_number:
        volume, chapter = clean_input_chapter(volumes, chapter_number)
                   
        if volume:
            url = chapters[volume][chapter]
            download_chapter(manga_name, volume, chapter, url)
    else:
        for volume, chapters in sorted(volumes.iteritems(),
            key=lambda x: float(x[0])):
            for chapter, url in sorted(chapters.iteritems(),
                key=lambda x: float(x[0])):
                download_chapter(manga_name, volume, chapter, url)
            
    os.remove("page.html")

if __name__ == '__main__':
    if len(sys.argv) == 5:
        download_manga_volume(sys.argv[1], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 4:
        if sys.argv[2].lower() == 'volume':
            download_manga_volume(sys.argv[1], sys.argv[3])
        else:
            download_manga_range(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        download_manga(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        download_manga(sys.argv[1])
    else:
        print("USAGE: mfdl.py [MANGA_NAME]")
        print("       mfdl.py [MANGA_NAME] [CHAPTER_NUMBER]")
        print("       mfdl.py [MANGA_NAME] [RANGE_START] [RANGE_END]")
