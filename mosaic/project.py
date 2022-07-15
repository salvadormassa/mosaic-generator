#!/usr/bin/env python3

from PIL import Image
import os
import time
import requests
from requests.exceptions import HTTPError
import shutil
import wget
import json
import re
import sys
# Beautiful Soup is a Python library for pulling data out of HTML and XML files.
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
from random import choice
#image.resize((#, #))

# If no command line arguments are given, this program will, by default,
# ask the user for an artist name and create an mosaic of  a
# self portrait by that artist using that artists own art.


def get_input():
    """
    Gets user input for artist name.
    """

    while True:
        user_input = input().lower().strip()
        if user_input == "":
            continue
        artist_name = user_input.replace(" ", "+")
        break

    return artist_name


def download_image(url):
    """
    Downloads an image from url.
    Returns the file name.
    """

    filename = url.split("/")[-1]
    r = requests.get(url, stream = True)
    # Check if the image was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission.
        with open(filename,'wb') as f:
            shutil.copyfileobj(r.raw, f)

        print('Portrait Downloaded: ',filename)
    else:
        print('Image Couldn\'t be retreived')

    return filename


def get_portrait(url):
    """
    Take user input of an artist and finds a self portrait of that artist.
    If there are more than one self portrait, picks a random one.
    """

    print("Finding portrait.")
    portrait_url = "https://www.wga.hu/art/{}"
    try:
        response = requests.get(url)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    soup = str(bs(requests.get(url).content, "html.parser"))
    regex = r'href="\/art\/([\/\w\.]*)"'

    # Check if any portraits are found.
    try:
        self_portrait = choice(re.findall(regex, soup))
    except IndexError:
        sys.exit("No portraits found.")

    portrait_url = portrait_url.format(self_portrait)
    filename = download_image(portrait_url)

    return filename

def valid_url(url):
    """
    Checks if a url is valid.
    """

    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_thumbnail_urls(url):
    """
    Returns all image URLs in a list.
    """

    soup = bs(requests.get(url).content, "html.parser")

    url_list = []
    for img in soup.find_all("img", src=re.compile('.*\.jpg', re.IGNORECASE)):
        img_url = img.get("src")

        # If img does not contain src attribute, then skip.
        if not img_url:
            continue

        # Takes the url and cuts off the "base" component,
        # then attaches it to the image url.
        img_url = urljoin(url, img_url)

        if valid_url(img_url):
            url_list.append(img_url)

    if url_list == 0:
        sys.exit("No thumbnails found.")

    return url_list

def download_thumbnails(url, pathname):
    """
    Downloads the thumbnail image.
    """

    # Checks if artist directory exists
    # If not, creates one
    if not os.path.exists(pathname):
        os.mkdir(pathname)
    # Check if there are files already in pathname
    # If so, exists function
    if len(pathname) > 0:
        return

    response = requests.get(url)
    filename = os.path.join(pathname, url.split("/")[-1])


    # This is very slow, needs to be faster
    with open(filename, "wb") as file:
        file.write(response.content)

def get_rgb(img_object):
    """
    Generate a 3 tuple numerical value (red, green, blue)
    for each pixel in an image and returns the average value.
    """

    rgb_list = list(img_object.getdata())
    pixels = len(rgb_list)
    r, g, b = 0, 0, 0
    for pixel in rgb_list:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    average_rgb = [int(r/pixels), int(g/pixels), int(b/pixels)]
    return average_rgb


def get_thumbnail_avg_ratio(pathname):
    """
    Gets the average aspect ratio of all thumbnails.
    Example: height 1.2, width 0.8
    """

    ratio = 0
    for file in os.listdir(pathname):
        file = pathname+"/"+file
        with Image.open(file).convert("RGB") as im:
            ratio += im.height/im.width

    height = round(ratio/len(os.listdir(pathname)), 3)
    width = round(((1 - height) + 1), 3)

    return height, width


def get_tile_dimensions(ratio_height, ratio_width, portrait):
    """
    Using the average thumbnail ratio,
    Get the tile pixel width and height using the portrait.
    """

    # 32 is derived from 32x32=1024 on a square,
    # which is roughly how many tiles that look good for a mosaic
    with Image.open(portrait).convert("RGB") as im:
        # Calculates pixel width and height based on ratios
        pixel_height = round(im.height * ratio_height / 32)
        pixel_width = round(im.width * ratio_width / 32)

    return pixel_height, pixel_width


def create_tiles(portrait, pathname):
    """
    Resizes thumbnails using get_tile_dimensions().
    """

    # Creates a directory to hold tiles if it does not exist
    tile_dir = pathname+"_tiles"
    if not os.path.exists(tile_dir):
        os.mkdir(tile_dir)

    # Gets the average ratio from thumbnails
    ratio_height, ratio_width = get_thumbnail_avg_ratio(pathname)

    # Gets the dimensions
    size = get_tile_dimensions(ratio_height, ratio_width, portrait)
    print(size)

    # Resizes tiles and saves to a new directory
    for file in os.listdir(pathname):
        filename = pathname+"/"+file
        with Image.open(filename).convert("RGB") as im:
            im1 = im.resize(size)
            im1.save(tile_dir+"/"+file, "JPEG")


def divide_portrait(ratio_height, ratio_width, portrait):
    """
    Takes the average ratio size of thumbnails
    and calculates the pixel width and height using the portrait.
    """

    im_dict = {}
    with Image.open(portrait).convert("RGB") as im:
        # Calculates how many rows and columns are needed
        rows = round(im.height / (32 * height))
        columns = round(im.width / (32 * width))

        # Think of grid where origin is top left on image
        for a in range(columns):
            for b in range(rows):
                top = int(im.height/32) * a # x
                left = int(im.width/32) * b # y
                bottom = int(im.height/32) * (a + 1) # x
                right = int(im.width/32) * (b + 1) # y

                im1 = im.crop((left, top, right, bottom))
                # im1.show()
                if a + 1 not in im_dict:
                    im_dict[a + 1] = get_rgb(im1)
                else:
                    im_dict[a + 1] += get_rgb(im1)
        print(im_dict)
        

def main():
    cur_dir = os.getcwd()
    artist_name = "author="
    title = "title="
    url = "https://www.wga.hu/cgi-bin/search.cgi?{}&{}&comment=&time=any&school=any&form=any&type=any&location=&max=1000&format=5"

    # Only 0, 1, or 2 Command Line Arguments are valid.
    if len(sys.argv) > 3:
        sys.exit("You must have either 0, 1, or 2 command line arguments.")

    # If no CLA are given,
    # Program will ask for user input for an artist,
    # then generate a mosaic of a portrait of that artist.
    elif len(sys.argv) == 1:
        print("Name an artist to create a mosaic of: ", end="")
        user_input = get_input()

        artist_name = artist_name+user_input
        pathname = cur_dir+"/"+user_input.replace("+", "_")
        portrait_file = get_portrait(url.format(artist_name, title+"self+portrait"))

        thumbnail_list = get_thumbnail_urls(url.format(artist_name, title))
        for url in thumbnail_list:
            download_thumbnails(url, pathname)

        create_tiles(portrait_file, pathname)
        # divide_portrait(ratio_height, ratio_width, portrait_file)






    # # If 1 CLA is given, that CLA is for a local image to
    # # be made into a mosaic
    # elif len(sys.argv) == 2:
    #     file = cur_dir+"/"+sys.argv[1]
    #     if not os.path.exists(file):
    #         sys.exit(f"Could not find {sys.argv[1]}.")
    #
    #     user_input = input("Which artist's works would you like? ")
    #     artist_name = artist_name+get_input()
    #     url = url.format(artist_name, title)
    #
    #
    #     thumbnails = get_thumbnail_urls(url)
    #     for img in imgs:
    #         download_thumbnail(img, path)


    # # If 2 command line arguments are given.
    # # First CLA is the image that will be made into a mosaic.
    # # Second CLA is the thumbnail database.
    # elif len(sys.argv) == 3:
    #
    #     if not os.path.exists(sys.argv[2]):
    #         sys.exit(f"Could not find {sys.argv[1]}.")
    #     if not os.path.exists(sys.argv[3]):
    #         sys.exit(f"Could not find {sys.argv[2]}.")


if __name__ == "__main__":
    main()
