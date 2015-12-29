from __future__ import print_function
from django.core.management.base import BaseCommand
from ... import models as sa_models
import json
# for manually testing with `./manage.py shell` commandline:
# from sa_api_v2 import models as sa_models
# from sa_api_v2 import forms
from itertools import chain

import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update our rain garden numbers'

    def handle(self, *args, **options):
        # get our nonnumbered user-generated rain gardens:
        nonnumbered_user_generated = sa_models.Place.objects.exclude(
            data__contains='"rain_garden_number":').order_by('pk')

        # get our nonnumbered imported rain gardens:
        nonnumbered_imported = sa_models.Place.objects.filter(
            data__contains='"rain_garden_number": ""').order_by('pk')

        nonnumbered_rain_gardens = sorted(
            chain(nonnumbered_user_generated, nonnumbered_imported),
            key=lambda instance: instance.pk)

        # get our total number of rain gardens:
        places = sa_models.Place.objects.all()

        # For now, let's start where we left off: make the rain garden number
        # is the size of all rain gardens, minus the unnumbered rain gardens
        next_rain_garden_number = len(places) - len(nonnumbered_rain_gardens) + 1

        # traverse our nonnumbered_rain_gardens, in order of pk,
        # and give each rain garden a number
        for nonnumbered_rain_garden in nonnumbered_rain_gardens:
            print("updating nonnumbered_rain_garden:", nonnumbered_rain_garden)
            data = json.loads(nonnumbered_rain_garden.data)
            data['rain_garden_number'] = str(next_rain_garden_number)
            nonnumbered_rain_garden.data = json.dumps(data)
            nonnumbered_rain_garden.save()
            next_rain_garden_number += 1
            print("nonnumbered_rain_garden updated:", nonnumbered_rain_garden)
