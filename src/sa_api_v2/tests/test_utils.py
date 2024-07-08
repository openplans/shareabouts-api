# """
# This file demonstrates writing tests using the unittest module. These will pass
# when you run "manage.py test".

# Replace this with more appropriate tests for your application.
# """

from django.test import TestCase
from django.contrib.gis.measure import D
from .. import utils


class TestToDistance (TestCase):
    def test_no_units_assumes_meters(self):
        d = utils.to_distance('123.45')
        self.assertEqual(d, D(m=123.45))

    def test_units_are_respected(self):
        d = utils.to_distance('123.45 km')
        self.assertEqual(d, D(km=123.45))

        d = utils.to_distance('123.45mi')
        self.assertEqual(d, D(mi=123.45))


class TestBuildRelativeURL (TestCase):
    def test_relative_path_with_leading_slash(self):
        url = utils.build_relative_url('http://ex.co/pictures/silly/abc.png', '/home')
        self.assertEqual(url, 'http://ex.co/home')

    def test_relative_path_without_leading_slash(self):
        url = utils.build_relative_url('http://ex.co/p/index.html', 'about.html')
        self.assertEqual(url, 'http://ex.co/p/about.html')

    def test_relative_path_empty(self):
        url = utils.build_relative_url('http://ex.co/p/index.html', '')
        self.assertEqual(url, 'http://ex.co/p/index.html')

    def test_original_path_ends_with_slash(self):
        url = utils.build_relative_url('http://ex.co/p/', 'about.html')
        self.assertEqual(url, 'http://ex.co/p/about.html')

    def test_leading_slash_beats_trailing_slash(self):
        url = utils.build_relative_url('http://ex.co/pictures/silly/', '/home')
        self.assertEqual(url, 'http://ex.co/home')

    def test_original_path_empty(self):
        url = utils.build_relative_url('', 'about.html')
        self.assertEqual(url, '/about.html')

    def test_relative_path_is_actually_full_url(self):
        url = utils.build_relative_url('http://ex.co/', 'https://google.com/')
        self.assertEqual(url, 'https://google.com/')
