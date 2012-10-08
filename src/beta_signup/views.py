from django.conf import settings
from django.shortcuts import render_to_response


def index(request):
    return render_to_response('index.html', {'LAUNCHROCK_KEY': settings.LAUNCHROCK_KEY})
