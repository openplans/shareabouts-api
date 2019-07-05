from django.conf.urls import url, include
from django.contrib.auth.views import login
from django.http import HttpResponse
from . import views
import rest_framework.urls
import social_django.urls


urlpatterns = [
    url(r'^$',
        views.ShareaboutsAPIRootView.as_view(),
        name='api-root'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<thing_id>\d+)/attachments$',
        views.AttachmentListView.as_view(),
        name='place-attachments'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<thing_id>\d+)/attachments$',
        views.AttachmentListView.as_view(),
        name='submission-attachments'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/actions$',
        views.ActionListView.as_view(),
        name='action-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/metadata$',
        views.DataSetMetadataView.as_view(),
        name='dataset-metadata'),

    # bulk data snapshots

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)/snapshots$',
        views.DataSnapshotRequestListView.as_view(),
        name='dataset-snapshot-list'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)/snapshots/(?P<data_guid>[^/.]+)(:?\.(?P<format>[^/]+))?$',
        views.DataSnapshotInstanceView.as_view(),
        name='dataset-snapshot-instance'),

    # ad-hoc data

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<submission_id>\d+)$',
        views.SubmissionInstanceView.as_view(),
        name='submission-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.SubmissionListView.as_view(),
        name='submission-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)$',
        views.PlaceInstanceView.as_view(),
        name='place-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.PlaceListView.as_view(),
        name='place-list'),

    url(r'^~/datasets$',
        views.AdminDataSetListView.as_view(),
        name='admin-dataset-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/keys$',
        views.ApiKeyListView.as_view(),
        name='apikey-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/origins$',
        views.OriginListView.as_view(),
        name='origin-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.DataSetSubmissionListView.as_view(),
        name='dataset-submission-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)$',
        views.DataSetInstanceView.as_view(),
        name='dataset-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets$',
        views.DataSetListView.as_view(),
        name='dataset-list'),

    # profiles and user info

    url(r'^(?P<owner_username>[^/]+)$',
        views.UserInstanceView.as_view(),
        name='user-detail'),

    url(r'^(?P<owner_username>[^/]+)/password$',
        lambda *a, **k: None,
        name='user-password'),

    url(r'^users/current$',
        views.CurrentUserInstanceView.as_view(),
        name='current-user-detail'),

    # authentication / association

    url(r'^users/login/error/$', views.remote_social_login_error, name='remote-social-login-error'),
    url(r'^users/login/(?P<backend>[^/]+)/$', views.remote_social_login, name='remote-social-login'),
    url(r'^users/logout/$', views.remote_logout, name='remote-logout'),

    url('^users/', include(social_django.urls, namespace='social')),

    url(r'^forms/', include(rest_framework.urls)),

    # Utility routes

    url(r'^utils/send-away', views.redirector, name='redirector'),
    url(r'^utils/session-key', views.SessionKeyView.as_view(), name='session-key'),
    url(r'^utils/noop/?$', lambda request: HttpResponse(''), name='noop-route'),

]

#places_base_regex = r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/places/'

#urlpatterns = patterns('sa_api_v2',
#    url(r'^$',
#        views.OwnerCollectionView.as_view(),
#        name='owner_collection'),

#    url(r'^(?P<owner__username>[^/]+)/datasets/$',
#        views.DataSetCollectionView.as_view(),
#        name='dataset_collection_by_user'),

#    url(r'^(?P<owner__username>[^/]+)/datasets/(?P<slug>[^/]+)/$',
#        views.DataSetInstanceView.as_view(),
#        name='dataset_instance_by_user'),

#    url(r'^(?P<datasets__owner__username>[^/]+)/datasets/(?P<datasets__slug>[^/]+)/keys/$',
#        views.ApiKeyCollectionView.as_view(),
#        name='api_key_collection_by_dataset'),

#    url(places_base_regex + '$',
#        views.PlaceCollectionView.as_view(),
#        name='place_collection_by_dataset'),

#    url(places_base_regex + 'table$',
#        views.TabularPlaceCollectionView.as_view(),
#        name='tabular_place_collection_by_dataset'),

#    url(places_base_regex + r'(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance_by_dataset'),

#    url(places_base_regex + r'(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='place_attachment_by_dataset'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/$',
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection_by_dataset'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularSubmissionCollectionView.as_view(),
#        name='tabular_submission_collection_by_dataset'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<pk>\d+)/$',
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance_by_dataset'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='submission_attachment_by_dataset'),

#    url(r'^(?P<data__dataset__owner__username>[^/]+)/datasets/(?P<data__dataset__slug>[^/]+)/actions/$',
#        views.ActionListView.as_view(),
#        name='action_collection_by_dataset'),

#    url(r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/$',
#        views.AllSubmissionCollectionsView.as_view(),
#        name='all_submissions_by_dataset'),

#    url(r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularAllSubmissionCollectionsView.as_view(),
#        name='tabular_all_submissions_by_dataset'),

#    url(r'^(?P<owner__username>[^/]+)/password$',
#        views.OwnerPasswordView.as_view(),
#        name='owner_password'),
#)

#places_base_regex = r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/places/'

#urlpatterns += patterns('sa_api_v2',

#    ###############################################
#    # URL patterns with 'datasets/' before user name. Deprecate.

#    url(r'^datasets/(?P<owner__username>[^/]+)/$',
#        views.DataSetCollectionView.as_view(),
#        name='dataset_collection_by_user_1'),

#    url(r'^datasets/(?P<owner__username>[^/]+)/(?P<slug>[^/]+)/$',
#        views.DataSetInstanceView.as_view(),
#        name='dataset_instance_by_user_1'),

#    url(r'^datasets/(?P<datasets__owner__username>[^/]+)/(?P<datasets__slug>[^/]+)/keys/$',
#        views.ApiKeyCollectionView.as_view(),
#        name='api_key_collection_by_dataset_1'),

#    url(places_base_regex + '$',
#        views.PlaceCollectionView.as_view(),
#        name='place_collection_by_dataset_1'),

#    url(places_base_regex + 'table$',
#        views.TabularPlaceCollectionView.as_view(),
#        name='tabular_place_collection_by_dataset_1'),

#    url(places_base_regex + r'(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance_by_dataset_1'),

#    url(places_base_regex + r'(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='place_attachment_by_dataset_1'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/$',
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection_by_dataset_1'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularSubmissionCollectionView.as_view(),
#        name='tabular_submission_collection_by_dataset_1'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<pk>\d+)/$',
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance_by_dataset_1'),

#    url(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='submission_attachment_by_dataset_1'),

#    url(r'^datasets/(?P<data__dataset__owner__username>[^/]+)/(?P<data__dataset__slug>[^/]+)/action/$',
#        views.ActionListView.as_view(),
#        name='action_collection_by_dataset_1'),

#    url(r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/$',
#        views.AllSubmissionCollectionsView.as_view(),
#        name='all_submissions_by_dataset_1'),

#    url(r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularAllSubmissionCollectionsView.as_view(),
#        name='tabular_all_submissions_by_dataset_1'),


#    ###############################################
#    # Views with no specified dataset. Deprecate.

#    url(r'^places/(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance'),

#    url((r'^places/(?P<place_id>\d+)/'
#         r'(?P<submission_type>[^/]+)/$'),
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection'),
#    url((r'^places/(?P<place_id>\d+)/'
#         r'(?P<submission_type>[^/]+)/(?P<pk>\d+)/$'),
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance'),

#    url(r'^action/$',
#        views.ActionListView.as_view(),
#        name='action_collection'),
#)
