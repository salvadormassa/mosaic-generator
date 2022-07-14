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
from tqdm import tqdm
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
        user_input = input("Name an artist to create a mosaic of: ").lower().strip()
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

    portrait_url = "https://www.wga.hu/art/{}"
    while True:
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
            break
        except IndexError:
            sys.exit("No portraits found.")

    portrait_url = portrait_url.format(self_portrait)
    filename = download_image(portrait_url)

    return filename


def chunk():
    """
    Takes an image and splits it into 1024 (arbitrary) pieces.
    Then run get_rgb() on each piece.
    """

    im_dict = {}
    with Image.open(infile).convert("RGB") as im:
        # print(im.size)
        # Think of grid where origin is top left on image
        for a in range(32):
            for b in range(32):
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


def create_thumbnail():
    """
    Creates a thumbnail of a JPEG,
    preserving aspect ratios with 128x128 max resolution.
    """

    infile = "Monet_Veduta_di_Rouelles.jpg"
    size = 128, 128

    # file, ext = os.path.splitext(infile)
    with Image.open(infile).convert("RGB") as im:
        im.thumbnail(size)
        print(len(list(im.getdata())))
        avg_rgb = get_rgb(im)
        im.save(f"1_{avg_rgb[0]}_{avg_rgb[1]}_{avg_rgb[2]}" + ".thumbnail", "JPEG")


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


def main():
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
        artist_name = artist_name+get_input()
        title = title+"self+portrait"
        url = url.format(artist_name, title)
        filename = get_portrait(url)

        # add get_thumbnails()

    # If 1 CLA is given, that CLA is for a local image to
    # be made into a mosaic
    elif len(sys.argv) == 2:
        if not os.path.exists(sys.argv[1]):
            sys.exit(f"Could not find {sys.argv[2]}.")

        # add get_thumbnails()


    # If 2 command line arguments are given.
    # First CLA is the image that will be made into a mosaic.
    # Second CLA is the thumbnail database.
    elif len(sys.argv) == 3:
        if not os.path.exists(sys.argv[2]):
            sys.exit(f"Could not find {sys.argv[1]}.")
        if not os.path.exists(sys.argv[3]):
            sys.exit(f"Could not find {sys.argv[2]}.")


if __name__ == "__main__":
    main()
