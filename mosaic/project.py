#!/usr/bin/env python3

from PIL import Image
import os
import subprocess
import requests
from requests.exceptions import HTTPError
import shutil
import json
import re
import sys
import time
# Beautiful Soup is a Python library for pulling data out of HTML and XML files.
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
from random import choice
# Adds progress meter to iterations
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
# Adds ability to pool.map to use functions with multiple arguments
from functools import partial
# from memory_profiler import memory


# Value to input into equations to calculate the number of tiles
tile_num = 20

def get_input():
    """
    Gets user input for artist name.
    """

    while True:
        user_input = input("Input a famous classical painter: ").lower().strip()
        if user_input == "":
            continue
        break

    return user_input


def validate_url(url):
    """
    Tests a URL for errors.
    """

    try:
        response = requests.get(url)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_error:
        sys.exit(f'HTTP error occurred: {http_error}')
    except Exception as error:
        sys.exit(f'Error: {error}')


def download_image(url, pathname=""):
    """
    Downloads image to path.
    If no pathname given, downloads to current directory.
    """
    filename = url.split("/")[-1]
    response = requests.get(url, stream = True)
    # Check if the image was retrieved successfully
    if response.status_code == 200:
        # Set decode_content value to True,
        # otherwise the downloaded image file's size will be zero.
        response.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission.
        with open(os.path.join(pathname, filename),'wb') as file:
            shutil.copyfileobj(response.raw, file)

    return filename


def get_portrait(url):
    """
    Take user input of an artist and finds a self portrait of that artist.
    If there are more than one self portrait, picks a random one.
    """

    # Gets URL content and converts to a string
    soup = str(bs(requests.get(url).content, "html.parser"))

    # Check if any portraits are found.
    print("Finding portrait.")
    try:
        # Finds all portrait url paths
        # If more than one, picks a random one
        regex = r'href="\/art\/([\/\w\.]*\.jpg)"'
        self_portrait = choice(re.findall(regex, soup))
    except IndexError:
        sys.exit("No portraits found.")

    portrait_url = f"https://www.wga.hu/art/{self_portrait}"

    return download_image(portrait_url)


def get_thumbnail_urls(url):
    """
    Opens URL and finds all .jpg instances and those URLs to a list.
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
        url_list += [img_url]

    if url_list == 0:
        sys.exit("No artist paintings found.")

    return url_list


def get_tile_dimensions(portrait):
    """
    Using the average thumbnail ratio,
    Get the tile pixel width and height using the portrait.
    """

    # which is roughly how many tiles that look good for a mosaic
    with Image.open(portrait).convert("RGB") as im:
        # Given a known amount of squares (tile_num),
        # Find how how many rows and columns in a renctangle
        ratio = im.height/im.width
        columns = im.width/tile_num
        rows = columns*ratio
        size = round(im.height/rows)
        size = (size, size)

    return size


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
    json_filename = os.path.basename(pathname).split(".")[0]+"_tiles.json"
    with open(json_filename, "w") as outfile:
        json.dump(tile_dict, outfile)

    return tile_dir, json_filename



def create_tiles(portrait, pathname, tile_url=""):
    """
    Resizes thumbnails using get_thumbnail_avg_ratio and
    get_tile_dimensions() fucntions.
    Creates RGB dictionary, saves to json, resizes and saves as tiles.
    """

    # Checks if artist directory exists
    # If not, creates one
    if not os.path.exists(pathname):
        os.mkdir(pathname)
    # Check if there are files already in pathname
    # If so, exists function
    if len(os.listdir(pathname)) == 0:
        # Get collection of art
        thumbnail_url_list = get_thumbnail_urls(tile_url)
        iter_list = iter(thumbnail_url_list)
        with Pool(cpu_count()) as p:
            print("Downloading thumbnails...")
            p.map(partial(download_image, pathname=pathname), thumbnail_url_list)

    # Derive dimensions from portrait
    square_size = get_tile_dimensions(portrait)

    # Creates RGB dictionary from tiles, saves to json file
    # Resizes and save tiles to new directory
    tile_dir, json_filename = create_dict_resize_save_tiles(square_size, pathname)

    return tile_dir, json_filename


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


def compose_mosaic(tile_dir, json_filename, portrait_file, image_name):
    """
    Breaks portrait into roughly 1000 rectangles.
    Uses json file to find best suited tile for each rectangle.
    Pastes each tile on best rentangle on a new portrait image.
    """

    print(f"Composing {image_name}")
    # with Image.open(portrait_file).convert("RGB") as im:
    #     copy_filename = "copy_of_"+portrait_file
    #     im1 = im.copy()
    #     im1.save(os.path.join(os.getcwd(), copy_filename), "JPEG")

    # Calculates how many rows and columns are needed
    with Image.open(portrait_file).convert("RGB") as im:
        ratio = im.height/im.width
        columns = im.width/tile_num
        rows = columns*ratio
        size = round(im.height/rows)
        rows = round(rows)
        columns = round(columns)

        # Think of grid where origin is top left on image
        with open(json_filename) as infile:
            tile_data = json.loads(infile.read())
            for a in range(rows):
                for b in range(columns):
                    best_match = ""
                    best_match_diff = 10000 # Arbitrary #, will be replaced with first iteration
                    top = int(size * a)# x
                    left = int(size * b) # y
                    bottom = int(size * (a + 1)) # x
                    right = int(size * (b + 1)) # y

                    coordinates = (left, top, right, bottom)
                    im1 = im.crop(coordinates)
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
                        im.paste(paste_image, coordinates)

        im_loc = os.path.join(os.getcwd()+"/mosaics", image_name+".jpg")
        im.save(im_loc, "JPEG")
        with Image.open(portrait_file).convert("RGB") as original:
            original.show(portrait_file)
        im.show(im_loc)

def file_cleanup(json_filename, tile_dir=""):
    """
    Removes json file and tile directory.
    """

    subprocess.run(["rm", json_filename])
    if os.path.exists(tile_dir):
        subprocess.run(["rm", "-r", tile_dir])


def main_no_arg():
    """
    Runs if no command line arguments are given.
    """

    artist = "author="
    title = "title="
    url = "https://www.wga.hu/cgi-bin/search.cgi?{}&{}&comment=&time=any&school=any&form=painting&type=any&location=&max=1000&format=5"

    # Get user input, compile and validate url
    user_input = get_input()
    image_name = user_input.replace(" ", "_")+"_mosaic"
    artist_name = artist+user_input
    portrait_url = url.format(artist_name.replace(" ", "+"), title+"self+portrait")
    validate_url(portrait_url)

    # Get portrait image
    portrait_file = get_portrait(portrait_url)

    # Get pathname for tile directory
    pathname = os.path.join(os.getcwd(), user_input.replace(" ", "_")+"_thumbnails")

    # Create the tiles
    tile_url = url.format(artist_name.replace(" ", "+"), title)
    tile_dir, json_filename = create_tiles(portrait_file, pathname, tile_url)

    # Compose the mosaic
    compose_mosaic(tile_dir, json_filename, portrait_file, image_name)

    # Remove files and directories
    file_cleanup(json_filename, tile_dir)


def verify_CLA(*args):
    """
    Verifies the command line argument(s) given by user.
    """

    valid_ext = ["jpg", "jpeg", "png"]
    try:
        # Argument 1 checks
        arg_1 = args[0][0]
        if not os.path.exists(arg_1):
            sys.exit(f"Could not find {arg_1}.")
        if os.path.getsize(arg_1) == 0:
            sys.exit(f"{arg_1} is an invalid file.")
        if args[1].split(".")[-1] not in valid_ext:
            sys.exit(f"{arg_1} is an invalid file type.")

        # Argument 2 checks
        arg_2 = args[0][1]
        if not os.path.exists(arg_2):
            sys.exit(f"Could not find {arg_2}.")
        if len(os.path.exists(arg_2)) == 0:
            sys.exit(f"There are no files in {arg_2}.")
    except IndexError:
        pass


def main_1_arg(portrait):
    """
    Runs if 1 command line argument is given.
    """

    url = "https://www.wga.hu/cgi-bin/search.cgi?author={}&title=&comment=&time=any&school=any&form=painting&type=any&location=&max=1000&format=5"

    # Get user input, compile and validate url
    user_input = get_input()
    name_split = portrait.split(".")
    image_name = name_split[0]+"_mosaic."+name_split[1]
    tile_dir = user_input.replace(" ", "_")
    artist_name = user_input.replace(" ", "+")
    url = url.format(user_input)
    validate_url(url)

    # Get pathname for tile directory
    pathname = os.path.join(os.getcwd(), tile_dir+"_thumbnails")

    # Create the tiles
    tile_url = url.format(user_input.replace(" ", "+"))
    tile_dir, json_filename = create_tiles(portrait, pathname, tile_url)

    # Compose the mosaic
    compose_mosaic(tile_dir, json_filename, portrait, image_name)

    # Remove files and directories
    file_cleanup(json_filename, tile_dir)


def main_2_arg(portrait, thumbnail_dir):
    """
    Runs if 2 command line arguments are given.
    """

    name_split = portrait.split(".")
    image_name = name_split[0]+"_mosaic."+name_split[1]

    # Create the tiles
    tile_dir, json_filename = create_tiles(portrait, thumbnail_dir)

    # Compose the mosaic
    compose_mosaic(tile_dir, json_filename, portrait, image_name)

    # Remove files and directories
    file_cleanup(json_filename, tile_dir)


def main():
    # Only 0, 1, or 2 Command Line Arguments are valid
    if len(sys.argv) > 3:
        sys.exit("You must have either 0, 1, or 2 command line arguments.")

    # If no command line args are given
    if len(sys.argv) == 1:
        main_no_arg()
        sys.exit()

    # Verify user command line arguments
    arguments = sys.argv[1:]
    verify_CLA(arguments)

    # If 1 command line arg is given
    if len(sys.argv) == 2:
        main_1_arg(arguments[0])
        sys.exit()

    # If 2 command line args are given
    if len(sys.argv) == 3:
        main_2_arg(arguments[0], arguments[1])
        sys.exit()


if __name__ == "__main__":
    # @profile
    main()
