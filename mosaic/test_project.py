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

import pytest
import mock

from project import get_input
from project import valid_url_tiles
from project import download_image
from project import verify_CLA
from project import get_portrait

# monkeypatch replaces the input() function, temporarily,
# with a string from the input list
def test_get_input_valid(monkeypatch):
    names = iter(["Claude Monet", "Vincent Van Gogh  ", " ", "    REMBRANDT", "      ", "\n", "leonardo DA VincI"])
    results = ["claude monet", "vincent van gogh", "rembrandt", "leonardo da vinci"]
    for result in results:
        monkeypatch.setattr('builtins.input', lambda: next(names))
        assert get_input() == result

def test_verify_CLA(monkeypatch):
    pathname = os.path.join(os.getcwd(), "test_files/test_images")
    for file in os.listdir(pathname):
        monkeypatch.setattr('sys.argv', [os.path.join(pathname, file), pathname])
        assert verify_CLA() == None

def test_get_portrait_invalid(capsys):
    with open("test_files/get_portrait_test_invalid.txt") as infile:
        reader = infile.readlines()
        for line in reader:
            with pytest.raises(SystemExit):
                assert get_portrait(line.strip()) == "No portraits found."
