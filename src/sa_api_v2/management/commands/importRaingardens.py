from __future__ import print_function
from django.core.management.base import BaseCommand
import csv
import sys
from ... import models as sa_models
from ... import forms
# for manually testing with `./manage.py shell` commandline:
# from sa_api_v2 import models as sa_models
# from sa_api_v2 import forms
import datetime
import json
from django.core.files import File
import os
import urllib

import logging
log = logging.getLogger(__name__)

csv_filepathname = sys.argv[2]


class Command(BaseCommand):
    help = 'Import a CSV file of places.'

    def handle(self, *args, **options):
        log.info('Command.handle: starting CSV import (log.info)')
        print('Command.handle: starting CSV import (print)')

        reader = csv.DictReader(open(csv_filepathname))
        i = 0
        for row in reader:
            if (i % 10 == 0):
                print("reading row", i)
            i += 1
            self.save_row(row)

    def save_row(self, row):
        lat = float(row['Lat'])
        lon = float(row['Long'])

        # create our data, used in Place for our dataset:
        location_type = 'raingarden'
        garden_size = row['Size (sq ft)']
        drainage_area = row['Drainage Area (sq ft)']
        designer = row['Designer']
        installer = row['Installer']

        description = row['Comments']
        if description == 'NULL':
            description = ''

        # TODO: create array of values when cell contains 'roof', 'pavement',
        #  or 'other'
        # shoud be case insensitive
        sources = row['Primary Sources']
        if sources == 'NULL':
            sources = ''

        street_address = row['Street Address ']
        if street_address == 'NULL':
            street_address = ''

        city = row['City']
        garden_address = ", ".join([street_address, city, 'WA'])

        # Imported rain gardens are unnamed
        site_name = ''

        # share_user_info_header = 'Please do not share any of my information,
        # I wish it to remain private'
        share_user_info_header = 'Remain Private'
        share_user_info = row[share_user_info_header] == 'NO'

        submitter_name = os.environ['RAIN_GARDENS_STEWARD_NAME']
        submitter_email = os.environ['RAIN_GARDENS_STEWARD_EMAIL']

        if (share_user_info and row['Name '] != '' and row['Email '] != ''):
            username = row['Name ']
            email = row['Email ']
        else:  # Not used because they are anonymous
            username = submitter_name
            email = submitter_email

        rain_garden_number = row['Rain Garden Number']

        data = {
            "gardensize": garden_size,
            "designer": designer,
            "private-garden_address": garden_address,
            "installer": installer,
            "contributing_area": drainage_area,
            "sources": sources,

            "description": description,
            "location_type": location_type,
            "garden_name": site_name,
            "private-submitter_email": email,
            "submitter_name": username,
            "garden_number": rain_garden_number
        }
        data = json.dumps(data)

        is_visible = (row["Approved to Show on Website"] == 'YES')
        placeForm = forms.PlaceForm({
            "data": data,
            # For geometry, using floats for lat/lon are accurate enough
            "geometry": "POINT(%f %f)" % (lon, lat),
            "created_datetime": datetime.datetime.now(),
            "updated_datetime": datetime.datetime.now(),
            "visible": is_visible
        })
        place = placeForm.save(commit=False)

        submitter = sa_models.User.objects.get(
            username=os.environ['RAIN_GARDENS_STEWARD_USERNAME']
        )
        place.submitter = submitter

        try:
            dataset = sa_models.DataSet.objects.get(slug='raingardens')
        except sa_models.DataSet.DoesNotExist:
            # query for the dataset
            dataset_owner = sa_models.User.objects.get(
                username=os.environ['DATASET_OWNER_NAME'],
                email=os.environ['DATASET_OWNER_EMAIL']
            )
            dataset = sa_models.DataSet(
                slug='raingardens',
                display_name='raingardens',
                owner=dataset_owner
            )
            print("existing dataset does not exist, creating new dataset:",
                  'raingardens')
            dataset.save()

        place.dataset = dataset

        place.save()

        imageUrl = row['Image']

        # TODO: Parallelize this!
        # TODO: Use pipe instead of saving/uploading file locally
        if imageUrl:
            file_name = "blob"
            content = urllib.urlretrieve(imageUrl, file_name)
            temp_file = File(open(content[0]))

            attachmentForm = forms.AttachmentForm({
                "created_datetime": datetime.datetime.now(),
                "updated_datetime": datetime.datetime.now(),
                "name": "my_image"
            }, {"file": temp_file})

            attachment = attachmentForm.save(commit=False)
            attachment.thing = place.submittedthing_ptr
            attachment.save()
            temp_file.close()
            os.remove(file_name)
