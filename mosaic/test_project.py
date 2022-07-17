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
from project import valid_url
from project import download_image
from project import verify_CLA

# monkeypatch replaces the input() function, temporarily,
# with a string from the input list
def test_get_input_valid(monkeypatch):
    names = ["Claude Monet", "Vincent Van Gogh  ", "    REMBRANDT", "leonardo DA VincI"]
    results = ["claude monet", "vincent van gogh", "rembrandt", "leonardo da vinci"]
    for (name, result) in zip(names, results):
        monkeypatch.setattr('builtins.input', lambda: name)
        assert get_input() == result

def test_valid_url():
    with open("test_files/url_test_list_validity.txt") as infile:
        reader = infile.readlines()
        for line in reader:
            assert valid_url(line.strip()) == True
