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


def valid_url(url):
    """
    Checks if a url is valid.
    """

    # Splits url into separate components
    parsed = urlparse(url)
    # Scheme is protocol (https), netloc is network location (www.google.com)
    return bool(parsed.netloc) and bool(parsed.scheme)


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
    except HTTPError as http_error:
        print(f'HTTP error occurred: {http_error}')
    except Exception as error:
        print(f'Other error occurred: {error}')

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



def get_thumbnail_urls(url):
    """
    Returns all image URLs in a list.
    """

    soup = bs(requests.get(url).content, "html.parser")

    url_list = []
    for img in soup.find_all("img", src=re.compile(".*\.jpg", re.IGNORECASE)):
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


def get_thumbnail_avg_ratio(pathname):
    """
    Gets the average aspect ratio of all thumbnails.
    Example: height 1.2, width 0.8
    """

    ratio = 0
    for file in os.listdir(pathname):
        file = os.path.join(pathname, file)
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

    # which is roughly how many tiles that look good for a mosaic
    with Image.open(portrait).convert("RGB") as im:
        # Calculates pixel width and height based on ratios
        pixel_height = round(im.height / (ratio_height * 32))
        pixel_width = round(im.width / (ratio_width * 32))

    return pixel_height, pixel_width


def create_dict_resize_save_tiles(size, pathname):
    """
    Resizes tiles, gets the rgb and saves to dict.
    Saves file to new directory.
    """

    # Creates a directory to hold tiles if it does not exist
    tile_dir = pathname+"_tiles"
    if not os.path.exists(tile_dir):
        os.mkdir(tile_dir)

    # Resizes tiles and saves to a directory
    tile_dict = {}
    for file in os.listdir(pathname):
        filename = os.path.join(pathname, file)
        with Image.open(filename).convert("RGB") as im:
            im1 = im.resize(size)
            # Get image average RGB while file is open, add to dictionary
            if filename not in tile_dict:
                tile_dict[file] = get_rgb(im1)
            # Save tile to new directory
            im1.save(os.path.join(tile_dir, file), "JPEG")

    # Save tile_dict to json file
    json_filename = os.path.basename(pathname).split(".")[0]
    with open(f"{json_filename}_tiles.json", "w") as outfile:
        json.dump(tile_dict, outfile)

    return tile_dir, json_filename



def create_tiles(portrait, pathname):
    """
    Resizes thumbnails using get_thumbnail_avg_ratio and
    get_tile_dimensions() fucntions.
    Creates RGB dictionary, saves to json, resizes and saves as tiles.
    """

    # Gets the average ratio from thumbnails
    ratio_height, ratio_width = get_thumbnail_avg_ratio(pathname)

    # Gets the dimensions
    size = get_tile_dimensions(ratio_height, ratio_width, portrait)

    # Creates RGB dictionary from tiles, saves to json file
    # Resizes and save tiles to new directory
    tile_dir, json_filename = create_dict_resize_save_tiles(size, pathname)

    return ratio_height, ratio_width, tile_dir, json_filename


def get_rgb(img_object):
    """
    Generates 3 numerical values (red, green, blue)
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


def compile_mosiac(ratio_height, ratio_width, tile_dir, json_filename, portrait_file):
    """
    Breaks portrait into roughly 1000 rectangles.
    Uses json file to find best suited tile for each rectangle.
    Pastes each tile on best rentangle on a new portrait image.
    """

    # Create a copy of portrait
    with Image.open(portrait_file).convert("RGB") as im:
        copy_filename = "copy_of_"+portrait_file
        im1 = im.copy()
        im1.save(os.path.join(os.getcwd(), copy_filename), "JPEG")

    with Image.open(copy_filename).convert("RGB") as copy_image:
        # Calculates how many rows and columns are needed
        rows = round(copy_image.height / (ratio_height * 32))
        columns = round(copy_image.width / (ratio_width * 32))
        print(rows, columns)

        # Think of grid where origin is top left on image
        with open("tile_dictionary.json") as infile:
            tile_data = json.loads(infile.read())
            for a in range(rows):
                for b in range(columns):
                    best_match = ""
                    best_match_diff = 10000
                    top = columns * a # x
                    left = rows * b # y
                    bottom = columns * (a + 1) # x
                    right = rows * (b + 1) # y

                    coordinates = (left, top, right, bottom)
                    im1 = copy_image.crop(coordinates)
                    portrait_rgb = get_rgb(im1)
                    portrait_rgb = portrait_rgb[0]+portrait_rgb[1]+portrait_rgb[2]


                    # Iterate through tile_data and compare to portrait
                    # Which ever number is closest wins
                    for i in tile_data:
                        tile_rgb = tile_data[i][0]+tile_data[i][1]+tile_data[i][2]
                        if tile_rgb > portrait_rgb:
                            diff = tile_rgb - portrait_rgb
                        else:
                            diff = portrait_rgb - tile_rgb

                        if diff < best_match_diff:
                            best_match_diff = diff
                            best_match = i

                    paste_path = os.path.join(tile_dir, best_match)
                    with Image.open(paste_path).convert("RGB") as paste_image:
                        copy_image.paste(paste_image, coordinates)

        file = "new_"+copy_filename
        copy_image.save(os.path.join(os.getcwd(), file), "JPEG")


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
        print("Name an artist to create a mosaic of: ", end="")
        user_input = get_input()

        artist_name = artist_name+user_input
        pathname = os.path.join(os.getcwd(), user_input.replace("+", "_"))
        portrait_file = get_portrait(url.format(artist_name, title+"self+portrait"))

        thumbnail_list = get_thumbnail_urls(url.format(artist_name, title))
        for url in thumbnail_list:
            download_thumbnails(url, pathname)

        ratio_height, ratio_width, tile_dir, json_filename = create_tiles(portrait_file, pathname)

        compile_mosiac(ratio_height, ratio_width, tile_dir, json_filename, portrait_file)






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
