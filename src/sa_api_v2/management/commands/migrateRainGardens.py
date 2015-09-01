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
        garden_size = validate(row['Rain garden Size (sq ft)'])
        drainage_area = validate(row['Contributing Area (sq ft)'])
        designer = validate(row['Designer'])
        installer = validate(row['Installer'])
        remain_private = row['Remain Private']

        description = row['Description']

        # Create array of values when cell contains 'roof', 'pavement',
        #  or 'other'
        raw_sources = row['Primary Sources'].lower().split(' ')
        possible_sources = {"driveway": "pavement",
                            "street": "pavement",
                            "roof": "roof",
                            "pavement": "pavement",
                            "garden": "other",
                            "other": "other"
                            }
        sources = set()
        for source in raw_sources:
            try:
                sources.add(possible_sources[source])
            except KeyError:
                continue
        sources = list(sources)

        street_address = row['Street Address']
        city = row['City']
        zip_code = row['Zip Code']

        full_address = [street_address, city, 'WA', zip_code]
        filtered_full_address = [x for x in full_address
                                 if (x and x != 'NULL')]
        garden_address = ", ".join(filtered_full_address)

        rain_garden_name = row['Rain Garden Name']

        # share_user_info_header = 'Please do not share any of my information,
        # I wish it to remain private'
        # TODO: For now, if rain gardens are private, we assume
        # all sensitive info is removed from source file
        share_user_info_header = 'Remain Private'
        remain_private = row[share_user_info_header] == 'YES'

        submitter_name = os.environ['RAIN_GARDENS_STEWARD_NAME']
        submitter_email = os.environ['RAIN_GARDENS_STEWARD_EMAIL']

        if (row['Contributor\'s Name'] != '' and row['Email'] != ''):
            username = row['Contributor\'s Name']
            email = row['Email']
        else:  # Use our defaults when username and email are not provided
            username = submitter_name
            email = submitter_email

        rain_garden_number = row['Rain Garden Number']

        data = {
            "rain_garden_size": garden_size,
            "designer": designer,
            "private-rain_garden_address": garden_address,
            "installer": installer,
            "contributing_area": drainage_area,
            "sources": sources,

            "description": description,
            "location_type": location_type,
            "rain_garden_name": rain_garden_name,
            "private-contributor_email": email,
            "contributor_name": username,
            "rain_garden_number": rain_garden_number,
            "remain_private": remain_private
        }
        data = json.dumps(data)

        placeForm = forms.PlaceForm({
            "data": data,
            # For geometry, using floats for lat/lon are accurate enough
            "geometry": "POINT(%f %f)" % (lon, lat),
            "created_datetime": datetime.datetime.now(),
            "updated_datetime": datetime.datetime.now(),
            "visible": True
        })
        place = placeForm.save(commit=False)

        try:
            submitter = sa_models.User.objects.get(
                username=username,
                email=email
            )
        except sa_models.User.DoesNotExist:
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


def validate(value):
    if value == 'NULL':
        return ''
    else:
        return value
