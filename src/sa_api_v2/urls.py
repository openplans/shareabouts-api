from django.conf.urls import include
from django.http import HttpResponse
from django.urls import re_path
from . import views
import rest_framework.urls
import social_django.urls


urlpatterns = [
    re_path(r'^$',
        views.ShareaboutsAPIRootView.as_view(),
        name='api-root'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<thing_id>\d+)/attachments$',
        views.AttachmentListView.as_view(),
        name='place-attachments'),
    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<thing_id>\d+)/attachments$',
        views.AttachmentListView.as_view(),
        name='submission-attachments'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/actions$',
        views.ActionListView.as_view(),
        name='action-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/metadata$',
        views.DataSetMetadataView.as_view(),
        name='dataset-metadata'),

    # bulk data snapshots

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)/snapshots$',
        views.DataSnapshotRequestListView.as_view(),
        name='dataset-snapshot-list'),
    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)/snapshots/(?P<data_guid>[^/.]+)(:?\.(?P<format>[^/]+))?$',
        views.DataSnapshotInstanceView.as_view(),
        name='dataset-snapshot-instance'),

    # ad-hoc data

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<submission_id>\d+)$',
        views.SubmissionInstanceView.as_view(),
        name='submission-detail'),
    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.SubmissionListView.as_view(),
        name='submission-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)$',
        views.PlaceInstanceView.as_view(),
        name='place-detail'),
    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.PlaceListView.as_view(),
        name='place-list'),

    re_path(r'^~/datasets$',
        views.AdminDataSetListView.as_view(),
        name='admin-dataset-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/keys$',
        views.ApiKeyListView.as_view(),
        name='apikey-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/origins$',
        views.OriginListView.as_view(),
        name='origin-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)(?:/(?P<pk_list>(?:\d+,)+\d+))?$',
        views.DataSetSubmissionListView.as_view(),
        name='dataset-submission-list'),

    re_path(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)$',
        views.DataSetInstanceView.as_view(),
        name='dataset-detail'),
    re_path(r'^(?P<owner_username>[^/]+)/datasets$',
        views.DataSetListView.as_view(),
        name='dataset-list'),

    # profiles and user info

    re_path(r'^(?P<owner_username>[^/]+)$',
        views.UserInstanceView.as_view(),
        name='user-detail'),

    re_path(r'^(?P<owner_username>[^/]+)/password$',
        lambda *a, **k: None,
        name='user-password'),

    re_path(r'^users/current$',
        views.CurrentUserInstanceView.as_view(),
        name='current-user-detail'),

    # authentication / association

    re_path(r'^users/login/error/$', views.remote_social_login_error, name='remote-social-login-error'),
    re_path(r'^users/login/(?P<backend>[^/]+)/$', views.remote_social_login, name='remote-social-login'),
    re_path(r'^users/logout/$', views.remote_logout, name='remote-logout'),

    re_path('^users/', include(social_django.urls, namespace='social')),

    re_path(r'^forms/', include(rest_framework.urls)),

    # Utility routes

    re_path(r'^utils/send-away', views.redirector, name='redirector'),
    re_path(r'^utils/session-key', views.SessionKeyView.as_view(), name='session-key'),
    re_path(r'^utils/noop/?$', lambda request: HttpResponse(''), name='noop-route'),

]

#places_base_regex = r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/places/'

#urlpatterns = patterns('sa_api_v2',
#    re_path(r'^$',
#        views.OwnerCollectionView.as_view(),
#        name='owner_collection'),

#    re_path(r'^(?P<owner__username>[^/]+)/datasets/$',
#        views.DataSetCollectionView.as_view(),
#        name='dataset_collection_by_user'),

#    re_path(r'^(?P<owner__username>[^/]+)/datasets/(?P<slug>[^/]+)/$',
#        views.DataSetInstanceView.as_view(),
#        name='dataset_instance_by_user'),

#    re_path(r'^(?P<datasets__owner__username>[^/]+)/datasets/(?P<datasets__slug>[^/]+)/keys/$',
#        views.ApiKeyCollectionView.as_view(),
#        name='api_key_collection_by_dataset'),

#    re_path(places_base_regex + '$',
#        views.PlaceCollectionView.as_view(),
#        name='place_collection_by_dataset'),

#    re_path(places_base_regex + 'table$',
#        views.TabularPlaceCollectionView.as_view(),
#        name='tabular_place_collection_by_dataset'),

#    re_path(places_base_regex + r'(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance_by_dataset'),

#    re_path(places_base_regex + r'(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='place_attachment_by_dataset'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/$',
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection_by_dataset'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularSubmissionCollectionView.as_view(),
#        name='tabular_submission_collection_by_dataset'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<pk>\d+)/$',
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance_by_dataset'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='submission_attachment_by_dataset'),

#    re_path(r'^(?P<data__dataset__owner__username>[^/]+)/datasets/(?P<data__dataset__slug>[^/]+)/actions/$',
#        views.ActionListView.as_view(),
#        name='action_collection_by_dataset'),

#    re_path(r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/$',
#        views.AllSubmissionCollectionsView.as_view(),
#        name='all_submissions_by_dataset'),

#    re_path(r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularAllSubmissionCollectionsView.as_view(),
#        name='tabular_all_submissions_by_dataset'),

#    re_path(r'^(?P<owner__username>[^/]+)/password$',
#        views.OwnerPasswordView.as_view(),
#        name='owner_password'),
#)

#places_base_regex = r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/places/'

#urlpatterns += patterns('sa_api_v2',

#    ###############################################
#    # URL patterns with 'datasets/' before user name. Deprecate.

#    re_path(r'^datasets/(?P<owner__username>[^/]+)/$',
#        views.DataSetCollectionView.as_view(),
#        name='dataset_collection_by_user_1'),

#    re_path(r'^datasets/(?P<owner__username>[^/]+)/(?P<slug>[^/]+)/$',
#        views.DataSetInstanceView.as_view(),
#        name='dataset_instance_by_user_1'),

#    re_path(r'^datasets/(?P<datasets__owner__username>[^/]+)/(?P<datasets__slug>[^/]+)/keys/$',
#        views.ApiKeyCollectionView.as_view(),
#        name='api_key_collection_by_dataset_1'),

#    re_path(places_base_regex + '$',
#        views.PlaceCollectionView.as_view(),
#        name='place_collection_by_dataset_1'),

#    re_path(places_base_regex + 'table$',
#        views.TabularPlaceCollectionView.as_view(),
#        name='tabular_place_collection_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='place_attachment_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/$',
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularSubmissionCollectionView.as_view(),
#        name='tabular_submission_collection_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<pk>\d+)/$',
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance_by_dataset_1'),

#    re_path(places_base_regex + r'(?P<place_id>\d+)/(?P<submission_type>[^/]+)/(?P<thing_id>\d+)/attachments/$',
#        views.AttachmentView.as_view(),
#        name='submission_attachment_by_dataset_1'),

#    re_path(r'^datasets/(?P<data__dataset__owner__username>[^/]+)/(?P<data__dataset__slug>[^/]+)/action/$',
#        views.ActionListView.as_view(),
#        name='action_collection_by_dataset_1'),

#    re_path(r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/$',
#        views.AllSubmissionCollectionsView.as_view(),
#        name='all_submissions_by_dataset_1'),

#    re_path(r'^datasets/(?P<dataset__owner__username>[^/]+)/(?P<dataset__slug>[^/]+)/(?P<submission_type>[^/]+)/table$',
#        views.TabularAllSubmissionCollectionsView.as_view(),
#        name='tabular_all_submissions_by_dataset_1'),


#    ###############################################
#    # Views with no specified dataset. Deprecate.

#    re_path(r'^places/(?P<pk>\d+)/$',
#        views.PlaceInstanceView.as_view(),
#        name='place_instance'),

#    re_path((r'^places/(?P<place_id>\d+)/'
#         r'(?P<submission_type>[^/]+)/$'),
#        views.SubmissionCollectionView.as_view(),
#        name='submission_collection'),
#    re_path((r'^places/(?P<place_id>\d+)/'
#         r'(?P<submission_type>[^/]+)/(?P<pk>\d+)/$'),
#        views.SubmissionInstanceView.as_view(),
#        name='submission_instance'),

#    re_path(r'^action/$',
#        views.ActionListView.as_view(),
#        name='action_collection'),
#)
