from __future__ import print_function
from django.core.management.base import BaseCommand
import csv
from ... import models as sa_models
from ... import forms
import datetime
import json
from django.core.files import File
import os
import urllib

import logging
log = logging.getLogger(__name__)

csv_filepathname="raingardens.csv"

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
        lat=float(row['Lat'])
        long=float(row['Long'])

        site_name = 'raingarden'
        possible_names = ['Designer', 'Installer', 'Owner']
        for possible_name in possible_names:
            if row[possible_name]:
                site_name = row[possible_name]
                break

        imageUrl = row['Image']

        # create our data, used in Place for our dataset:
        location_type = 'raingarden'
        # TODO: fill in description with raingarden size, cost, etc
        size = row['Size (sq ft)']
        drainage_area = row['Drainage Area (sq ft)']
        primary_source = row['Primary Source']
        size = "size: " + size
        drainage_area = "drainage area: " + drainage_area
        primary_source = "primary source: " + primary_source
        # TODO: Create custom model for these fields
        # wsu_master_gardeners = row['WSU Master Gardeners']
        # raingardens_webiste = row['"12,000 Rain Garden Website"']
        # conservation_district =row['Conservation District']
        # county_surface_water_utility = row['County Surface Water Management Utility']
        # stewardship_partners = row['Stewardship Partners']
        # landscape_engineer_architect_installed = row['"Landscape, Engineer, or Architect professional "']

        description = "\n".join([size, drainage_area, primary_source])


        # TODO: add check for whether the user wants their info listed
        share_information_header = "Please do not share any of my information, I wish to remain private OR  Approved to Show on Website?"
        share_my_information = (row[share_information_header] == 'NO')
        if (share_my_information):
            username=row['Name ']
            email=row['Email ']
        else : # Not used because they are anonymous
            username = 'Raingardens Steward'
            email = 'jacob@smartercleanup.org'
        # create a User model (if none already existing):
        try:
            existing_user = sa_models.User.objects.get(username=username, email=email)
            user = existing_user
        except sa_models.User.DoesNotExist:
            user = sa_models.User(
                username = username,
                email = email
            )
            print("existing user does not exist, creating new user:", user)
            user.save()

        # query for the dataset
        # TODO: Find a way to load raingarden data dynamically
        # Using the same dataset across flavors will slow down all flavors
        dataset = sa_models.DataSet.objects.get(slug='duwamish')
        # dataset = sa_models.DataSet.objects.get(slug='raingardens')

        data = {
            "description": description,
            "location_type": location_type,
            "name": site_name,
            "private-submitter_email": email,
            "submitter_name": username
        }
        data = json.dumps(data)

        placeForm = forms.PlaceForm({
            "data":data,
            "geometry":"POINT(%f %f)" % (long, lat), # floats as coords are accurate enough
            "created_datetime": datetime.datetime.now(),
            "updated_datetime": datetime.datetime.now(),
            "visible": "True"
        })
        place = placeForm.save(commit=False)
        place.dataset = dataset
        place.submitter = user
        place.save()

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
