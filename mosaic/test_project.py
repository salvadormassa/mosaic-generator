#!/usr/bin/env python3

from PIL import Image
import os
import requests
from requests.exceptions import HTTPError
import shutil
import json
import re
import sys
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
from random import choice
# Testing imports
import pytest
import mock
# Functions tested
from project import get_input
from project import verify_CLA
from project import get_portrait
from project import get_rgb


# monkeypatch replaces the input() function, temporarily,
# with a string from the input list
def test_get_input_valid(monkeypatch):
    names = iter(["Claude Monet", "Vincent Van Gogh  ", " ", "    REMBRANDT", "      ", "\n", "leonardo DA VincI"])
    results = ["claude monet", "vincent van gogh", "rembrandt", "leonardo da vinci"]
    for result in results:
        monkeypatch.setattr('builtins.input', lambda _: next(names))
        assert get_input() == result

def test_verify_CLA_valid(monkeypatch):
    pathname = os.path.join(os.getcwd(), "test_files/test_images")
    for file in os.listdir(pathname):
        file = ["test", os.path.join(pathname, file)]
        monkeypatch.setattr('sys.argv', file)
        assert verify_CLA() == None

def test_get_portrait_valid(monkeypatch):
    with open("test_files/get_portrait_test_valid.txt") as infile:
        reader = infile.readlines()
        for line in reader:
            monkeypatch.setattr("project.download_image", lambda _: "example")
            assert get_portrait(line, "artist") == "example"

def test_get_portrait_invalid(capsys):
    with open("test_files/get_portrait_test_invalid.txt") as infile:
        reader = infile.readlines()
        for line in reader:
            with pytest.raises(SystemExit):
                assert get_portrait(line.strip(), "artist") == "No portraits found."

def test_get_rgb():
    path = os.path.join(os.getcwd(), "test_files/test_tiles")
    for image in os.listdir(path):
        with Image.open(os.path.join(path, image)).convert("RGB") as im:
            assert get_rgb(im) < [256, 256, 256] and get_rgb(im) > [0, 0, 0]
