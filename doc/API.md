Resources
=========

`:owner` refers to a username. `:ds-slug` is a dataset slug. `:ss-name` is the
name of a submission set. `:p-id` and `:s-id` are the numeric ids of a place
and a submission, respectively.

  * **/api/v1/** -- List of all the dataset owners
  * **/api/v1/*:owner*/datasets/** -- List of a user's owned datasets
  * **/api/v1/*:owner*/datasets/*:ds-slug*/** -- A specific dataset instance
  * **/api/v1/*:owner*/datasets/*:ds-slug*/places/** -- List of places in a
    dataset
  * **/api/v1/*:owner*/datasets/*:ds-slug*/places/*:p-id*/** -- A specific
    place instance
  * **/api/v1/*:owner*/datasets/*:ds-slug*/submissions/** -- List of all
    submissions in a dataset
  * **/api/v1/*:owner*/datasets/*:ds-slug*/*:ss-name*/** -- List of all
    submissions belonging to a particular submission set in a dataset
  * **/api/v1/*:owner*/datasets/*:ds-slug*/places/*:p-id*/submissions/** --
    List of all submissions attached to a place
  * **/api/v1/*:owner*/datasets/*:ds-slug*/places/*:p-id*/*:ss-name*/** -- List
    of all submissions belonging to a particular submission set attached to a
    place
  * **/api/v1/*:owner*/datasets/*:ds-slug*/places/*:p-id*/*:ss-name*/*:s-id*/**
    -- A specific submission instance

Datasets
--------

The primary entry point into the API is a dataset. Each dataset has an owner,
and a user can own any number of datasets.

To get a list of all datasets belonging to a user:

  * **Method**: GET

    **URL**: /api/v1/&lt;owner&gt;/datasets/

    **Result**: A list of JSON objects with the following fields:

      * *display_name*: the human-readable name for the dataset
      * *slug*: the short name for the dataset, used in the url; no user can
        own two datasets with the same slug
      * *id*: the numeric id of the dataset; every dataset has a unique id
      * *url*: the URL of the dataset
      * *owner*: an object with the `username` and `id` of the owner
      * *places*: an object with places metadata -- the number (`length`) of
        places, and the `url` of the place collection
      * *submissions*: a list of objects with meta data about each submission
        set -- `type` (the set name), `length`, and `url`
      * *keys*: an object that contains only the URL to the dataset's API keys

To create a new dataset:

  * **Method**: POST

    **URL**: /api/v1/&lt;owner&gt;/datasets/

    **Authentication**: Basic auth or session auth

    **Content type**: application/json

    **Fields**
      * *display_name*: the human-readable name for the dataset
      * *slug*: the short name for the dataset


Attachments
-----------

You can attach files to places and submissions.

  * **Method**: POST

    **URL**: /api/v1/&lt;owner&gt;/datasets/&lt;dataset&gt;/places/&lt;place&gt;/attachments/

    **Content type**: multipart/form-data

    **Fields**
      * *name*: The attachment's name -- should be unique within the place.
      * *file*: The attachment's file data.

    **Result**: A JSON object with the following fields:
      * *name*: The attachment's name
      * *url*: The URL of the attached file

For example, in Javascript (with jQuery), this can be done like:

    var data = new FormData();
    data.append('name', 'my-attachment')
    data.append('file', fileField.files[0])

    jQuery.ajax({
      url: '...',
      type: 'POST',
      data: data,

      contentType: false,
      processData: false
    });

Or, in Python, with requests:

    import requests
    requests.request(
        'POST',
        '...',
        data={'name': 'my-attachment'}
        files={'file': open('filename.jpg')}
    )
