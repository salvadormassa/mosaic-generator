#!/usr/bin/env python3

from PIL import Image
import os
import time
#image.resize((#, #))

infile = "Autoportret_Claude_Monet.jpg"

def chunk():
    """Takes an image and splits it into 1024 pieces.
    Then run get_rgb() on each piece."""

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
    """Creates a thumbnail of a JPEG,
    preserving aspect ratios with 128x128 max resolution."""

    infile = "Monet_Veduta_di_Rouelles.jpg"
    size = 128, 128

    # file, ext = os.path.splitext(infile)
    with Image.open(infile).convert("RGB") as im:
        im.thumbnail(size)
        print(len(list(im.getdata())))
        avg_rgb = get_rgb(im)
        im.save(f"1_{avg_rgb[0]}_{avg_rgb[1]}_{avg_rgb[2]}" + ".thumbnail", "JPEG")


def get_rgb(img_object):
    """Generate a 3 tuple numerical value (red, green, blue)
    for each pixel in an image and returns the average value."""

    rgb_list = list(img_object.getdata())
    pixels = len(rgb_list)
    r, g, b = 0, 0, 0
    for pixel in rgb_list:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    average_rgb = [int(r/pixels), int(g/pixels), int(b/pixels)]
    return average_rgb

create_thumbnail()
