from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('sa_api',
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<submission_id>\d+)$',
        views.SubmissionInstanceView.as_view(),
        name='submission-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)$',
        views.SubmissionListView.as_view(),
        name='submission-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)$',
        views.PlaceInstanceView.as_view(),
        name='place-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places$',
        views.PlaceListView.as_view(),
        name='place-list'),

    url(r'^~/datasets$',
        views.AdminDataSetListView.as_view(),
        name='admin-dataset-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/keys$',
        lambda *a, **k: None,
        name='apikey-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/(?P<submission_set_name>[^/]+)$',
        views.DataSetSubmissionListView.as_view(),
        name='dataset-submission-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)$',
        views.DataSetInstanceView.as_view(),
        name='dataset-detail'),
    url(r'^(?P<owner_username>[^/]+)/datasets$',
        views.DataSetListView.as_view(),
        name='dataset-list'),

    url(r'^(?P<owner_username>[^/]+)$',
        lambda *a, **k: None,
        name='user-detail'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/activity$',
        lambda *a, **k: None,
        name='action-list'),

    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/attachments$',
        lambda *a, **k: None,
        name='place-attachments'),
    url(r'^(?P<owner_username>[^/]+)/datasets/(?P<dataset_slug>[^/]+)/places/(?P<place_id>\d+)/(?P<submission_set_name>[^/]+)/(?P<submission_id>\d+)/attachments$',
        lambda *a, **k: None,
        name='submission-attachments'),

    url(r'^(?P<owner_username>[^/]+)/password$',
        lambda *a, **k: None,
        name='user-password'),

)

#places_base_regex = r'^(?P<dataset__owner__username>[^/]+)/datasets/(?P<dataset__slug>[^/]+)/places/'

#urlpatterns = patterns('sa_api',
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

#    url(r'^(?P<data__dataset__owner__username>[^/]+)/datasets/(?P<data__dataset__slug>[^/]+)/activity/$',
#        views.ActivityView.as_view(),
#        name='activity_collection_by_dataset'),

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

#urlpatterns += patterns('sa_api',

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

#    url(r'^datasets/(?P<data__dataset__owner__username>[^/]+)/(?P<data__dataset__slug>[^/]+)/activity/$',
#        views.ActivityView.as_view(),
#        name='activity_collection_by_dataset_1'),

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

#    url(r'^activity/$',
#        views.ActivityView.as_view(),
#        name='activity_collection'),
#)
