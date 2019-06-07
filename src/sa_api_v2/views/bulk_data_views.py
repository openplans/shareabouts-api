from django.core.urlresolvers import reverse
from django.http import HttpResponse
from mock import patch
from rest_framework import views, permissions
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException
from rest_framework.settings import APISettings
from rest_framework_bulk import generics as bulk_generics
from ..params import (INCLUDE_INVISIBLE_PARAM, INCLUDE_PRIVATE_PARAM,
    INCLUDE_SUBMISSIONS_PARAM, NEAR_PARAM, DISTANCE_PARAM, TEXTSEARCH_PARAM,
    FORMAT_PARAM, PAGE_PARAM, PAGE_SIZE_PARAM, CALLBACK_PARAM)
from ..models import DataSnapshotRequest, DataSnapshot, DataSet
from ..tasks import store_bulk_data, bulk_data_status_update
from .base_views import OwnedResourceMixin
import logging

log = logging.getLogger('sa_api_v2.views')


###############################################################################
#
# Resource Views
# --------------
#

class DataSnapshotMixin (object):
    response_messages = {
        'pending': 'You can download the data at the given URL when it is done being generated.',
        'success': 'You can download the data at the given URL.',
        'failure': 'There was an error generating the snapshot.',
    }

    def get_data_url(self, datarequest):
        data_url_kwargs = self.kwargs.copy()
        data_url_kwargs['data_guid'] = datarequest.guid
        data_url_kwargs.pop('format', None)
        path = reverse('dataset-snapshot-instance', kwargs=data_url_kwargs)
        url = self.request.build_absolute_uri(path)
        return url

    def get_data_description(self, datarequest):
        default_message = self.response_messages['pending']
        return {
            'status': datarequest.status,
            'message': self.response_messages.get(datarequest.status, default_message),
            'requested_at': datarequest.requested_at.isoformat(),
            'url': self.get_data_url(datarequest)
        }


class DataSnapshotRequestListView (DataSnapshotMixin, OwnedResourceMixin, views.APIView):
    """

    GET
    ---
    Get a list of your snapshots, including when they were generated.

    **Authentication**: Basic, session, or key auth *(required)*

    POST
    ----
    Make a new request for a data snapshot.

    **Authentication**: Basic, session, or key auth *(required)*

    ------------------------------------------------------------
    """
    # The first permission class in OwnedResourceMixin is IsOwnerOrReadOnly.
    # We don't want to impose that restriction on snapshot requests.
    permission_classes = OwnedResourceMixin.permission_classes[1:]
    submission_set_name_kwarg = 'submission_set_name'

    def get_method_actions(self):
        return {
            'GET': 'retrieve',
            'PUT': 'retrieve',
            'POST': 'retrieve'
        }

    def get_recent_requests(self, characteristic_params):
        return DataSnapshotRequest.objects\
            .all().order_by('-requested_at')\
            .filter(**characteristic_params)

    def get_most_recent_request(self, characteristic_params):
        try:
            return self.get_recent_requests(characteristic_params).filter(status='pending')[0]
        except IndexError:
            raise DataSnapshotRequest.DoesNotExist()

    def initiate_data_request(self, characteristic_params):
        # Create a new data request
        datarequest = DataSnapshotRequest(**characteristic_params)
        datarequest.requester = self.request.user if self.request.user.is_authenticated() else None
        datarequest.status = 'pending'
        datarequest.save()

        # Schedule the data to be generated and stored
        task = store_bulk_data.apply_async(args=(datarequest.pk,), link=bulk_data_status_update.s(), link_error=bulk_data_status_update.s())

        # Patch the task id on to the datarequest.
        datarequest.guid = task.id
        datarequest.save()

        # Return the data request
        return datarequest

    def get_characteristic_params(self, request, owner_username, dataset_slug, submission_set_name):
        """
        Get the parameters that should identify all snapshots formed off of
        this query.
        """
        params = request.GET if request.method.upper() == 'GET' else request.DATA
        return {
            'dataset': self.get_dataset(),
            'submission_set': submission_set_name,
            'include_private': str(params.get('include_private', False)).lower() not in ('f', 'false', 'off'),
            'include_invisible': str(params.get('include_invisible', False)).lower() not in ('f', 'false', 'off'),
            'include_submissions': str(params.get('include_submissions', False)).lower() not in ('f', 'false', 'off'),
        }

    def get_or_create_datarequest(self, request, owner_username, dataset_slug, submission_set_name):
        characteristic_params = self.get_characteristic_params(request, owner_username, dataset_slug, submission_set_name)

        try:
            datarequest = self.get_most_recent_request(characteristic_params)
        except DataSnapshotRequest.DoesNotExist:
            log.info('Initiating a new snapshot')
            datarequest = self.initiate_data_request(characteristic_params)
        else:
            log.info('Duplicate reqest for a new snapshot')

        return datarequest

    def post(self, request, owner_username, dataset_slug, submission_set_name):
        datarequest = self.get_or_create_datarequest(request, owner_username, dataset_slug, submission_set_name)
        return Response(self.get_data_description(datarequest), status=202)

    def get(self, request, owner_username, dataset_slug, submission_set_name):
        # Copy the query parameters, since we want to modify them
        request.GET = request.GET.copy()

        # Treat GET requests with a 'new' parameter like POST requests.
        if request.GET.pop('new', None) is not None:
            datarequest = self.get_or_create_datarequest(request, owner_username, dataset_slug, submission_set_name)
            return Response(self.get_data_url(datarequest), status=202)

        # Other requests get passed through
        characteristic_params = self.get_characteristic_params(request, owner_username, dataset_slug, submission_set_name)
        datarequests = self.get_recent_requests(characteristic_params)

        return Response([
            self.get_data_description(datarequest)
            for datarequest in datarequests], status=200)


class DataSnapshotInstanceView (DataSnapshotMixin, OwnedResourceMixin, views.APIView):
    """

    GET
    ---
    Get a specific data snapshot.

    **Authentication**: Basic, session, or key auth *(required)*

    DELETE
    ------
    Delete a snapshot and the corresponding request.

    **Authentication**: Basic, session, or key auth *(required)*

    ------------------------------------------------------------
    """
    submission_set_name_kwarg = 'submission_set_name'

    def get(self, request, owner_username, dataset_slug, submission_set_name, data_guid, format=None):
        # Get the snapshot request model
        try:
            datarequest = DataSnapshotRequest.objects.get(guid=data_guid)
        except DataSnapshotRequest.DoesNotExist:
            return Response({'status': 'not found', 'message': 'This data is no longer available'}, status=404)

        # Get the corresponding fulfillment of that request
        try:
            datarequest.fulfillment
        except DataSnapshot.DoesNotExist:
            if datarequest.status == 'failure':
                return Response(self.get_data_description(datarequest), status=404)
            else:
                return Response(self.get_data_description(datarequest), status=503)

        if format is None:
            format = 'json'

        if format not in ('json', 'geojson', 'csv'):
            return Response({
                'message': 'Invalid format: %s' % (format,)
            }, status=400)

        content = getattr(datarequest.fulfillment, format)
        if format == 'csv':
            mime = 'text/csv'
        else:
            mime = 'application/json'
        return HttpResponse(content, content_type=mime)

    def delete(self, request, owner_username, dataset_slug, submission_set_name, data_guid, format=None):
        try:
            datarequest = DataSnapshotRequest.objects.get(guid=data_guid)
        except DataSnapshotRequest.DoesNotExist:
            return Response(status=404)

        self.verify_object(datarequest.dataset, DataSet)
        try:
            datarequest.delete()
        finally:
            return Response(status=204)
