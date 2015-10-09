from __future__ import print_function
from django.core.management.base import BaseCommand
import csv
import sys

from ... import models as sa_models
from ... import forms

# for manually testing with django shell:
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


# TODO: Refactor common utils out of our import functions
class Command(BaseCommand):
    help = 'Import a CSV file of places.'

    def handle(self, *args, **options):
        log.info('Command.handle: starting CSV import (log.info)')
        print('Command.handle: starting CSV import (print)')

        reader = csv.DictReader(open(csv_filepathname))
        i = 0
        for row in reader:
            # if (i % 10 == 0):
            print("reading row", i)
            i += 1
            self.save_row(row)

    def save_row(self, row):

        # create our data, used in Place for our dataset:
        # images, street address, lat/lon, common name (title), latin name
        # (sub title / first line), tree condition (string)

        # Image URL|Common name|Latin Name|Tree ID Tag #|Family ID #|
        # First_Name|Last_Name|First_and_|Num|Street|Lat/Long|Phone|Email_addr|
        # Tree Condition|Water Bag?|Photo?|Notes_|||||||||||

        location_type = 'tree'
        lat, lon = [float(x) for x in row['Lat/Long'].split('/')]
        common_name = validate(row['Common name'])
        latin_name = validate(row['Latin Name'])
        condition = validate(row['Tree Condition'])
        notes = validate(row['Notes_'])
        waterbag = validate(row['Water Bag?'])
        family_id = validate(row['Family ID #'])

        # Private fields:
        id_tag = row['Tree ID Tag #']
        address = validate(row['Street'])
        submitter_email = validate(row['Email_addr'])
        phone = validate(row['Phone'])
        first_name = validate(row['First_Name'])
        last_name = validate(row['Last_Name'])

        print("processing tree id_tag:", id_tag)

        # Attachment data:
        imageUrl = validate(row['Image URL'])

        data = {
            "common_name": common_name,
            "latin_name": latin_name,
            "condition": condition,
            "location_type": location_type,
            "notes": notes,
            "waterbag": waterbag,
            "family_id": family_id,

            "private-id_tag": id_tag,
            "private-address": address,
            "private-submitter_email": submitter_email,
            "private-phone": phone,
            "private-first_name": first_name,
            "private-last_name": last_name
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

        submitter = sa_models.User.objects.get(username='DIRT_Corps')
        place.submitter = submitter

        dataset = sa_models.DataSet.objects.get(slug='trees')
        place.dataset = dataset

        place.save()

        # TODO: Parallelize this!
        # TODO: If possile, use pipe instead of saving/uploading file locally
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


# value must be a string
def validate(value):
    if value == 'NULL' or value.isspace():
        return ''
    else:
        return value
