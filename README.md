# Mosaic Generator
## Overview

This script creates a mosiac of an image using smaller images (tiles). It can accept 1 or 2 additional command line arguments.<br />
- If no arguments are given, the script will ask for user input for a painter. It will attempt to find a self-portrait of the painter to be made into a mosaic,
and also find the art from that painter to compose the mosaic.<br />
- The first optional argument should be a path to an image that will be used as the blueprint for the mosaic.  
- The second optional argument should be the path to a directory containing images that will be used to compose the mosaic.<br />
- If only the first argument is given, the script will then prompt the user for a painter whos art will compose the mosaic.  
## Technical Challenges
### Downloading Images  
The difficulty is to try and find a source that images can be reliably and consistantly downloaded. For this project I chose "classical art", 
as they would be in the public domain, and therefore have less restrictions on copyright.<br /><br />
Even though finding databases of classical art is easier than other types, it was still a challenge to acqure the necessary files for this 
program to work.<br /><br />
*Website used: https://www.wga.hu*  
: *The Web Gallery of Art is a virtual museum and searchable database of European fine arts, decorative arts and architecture (3rd-19th centuries), 
currently containing over 52.800 reproductions. Artist biographies, commentaries, guided tours, period music, catalogue, 
free postcard and mobile services are provided.*<br /><br />
This source allows files to be searched easily and images thumbnails can be downloaded instead of the full images, saving bandwidth.  
### Slow Downloads
Even though the thumbnails being downloading were relatively small, it was taking about a second per download. So to download a few hundred 
images would be minutes.<br /><br />
The solution was to use the Pool() function on the downloads, this drastically decreased to download window to a handful of seconds.
### Tile Size 
In developing this project, I learned about a technical problem called *rectangle packing*, or the *packing problem*. Which is the difficulty is 
trying to fit rectangles of various sizes into a larger rectangle, conserving the least amout of empty space. Needless to say this is a difficult 
problem, even without adding on the other problem of finding the best colored image for a particular space on 
the mosaic.<br /><br />
After researching this particular problem, my solution was just to avoid it. As that would be a worthy enough problem for a project on its own. 
Therefore, after downloading the required thumbnails, the program turns them into squares which I call *tiles* of equal size.  
### Breaking the Image into Components  
The next challenge was how to cut up the image that was going to be used for the mosaic template into individual pieces,  
that can be compared to the tiles. The challenge was for the program to be able to take images of various dimensions,  
and split them up, relatively, into a certain amount of tiles. This, like the packing problem, was harder than I anticipated.<br /><br />
The math involved here was a bit more than I would have hoped, and in the end I had to used a magic number approach. After running the program 
a few times and finding the "best" looking square density. I was able to find the best number of tiles per length/width, relatively speaking. 
Therefore I can use a "magic number", with some math, to give me and workable result.  
This leaves something to be desired for the usablility of the program, and is a core component that needs to be reworked.  
### Color Comparison  
The next challenge was how I was going to compare a *square* on the template image to the *database of tiles*. For this the program with will find the 
average red/green/blue numerical value for each tile and store it in a json file. In order to do this the program will iterate through each pixel 
on the tile, extracting the RGB value and then derive the average. It does the same for the square on the template image to will be replaced. 
When the program is replaces template image squares, it adds up the RGB as one number for both the square and tile, then finds the tile that is closest 
in value, and uses that tile as a replacement.<br /><br />
This seems to work relatively well, compared to its simplicity, although a better solution is no doubt probable.  
## Bugs
### Magic Number
This magic number approach does not scale accurately. The tiles on larger images will be too small, and the tiles on smaller images will be too large.  
## Additional Features to Add
- Add code to delete downloaded files.
- Progress meter on downloads/mosiac composition.
