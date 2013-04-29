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

**Fields**:

  * *id*: the numeric id of the dataset; every dataset has a unique id
  * *slug*: the short name for the dataset, used in the url; no user can
    own two datasets with the same slug
  * *display_name*: the human-readable name for the dataset
  * *url*: the URL of the dataset
  * *owner*: an object with the `username` and `id` of the owner
  * *places*: an object with places metadata -- the number (`length`) of
    places, and the `url` of the place collection
  * *submissions*: a list of objects with meta data about each submission
    set -- `type` (the set name), `length`, and `url`
  * *keys*: an object that contains only the URL to the dataset's API keys

### GET /api/v1/*:owner*/datasets/

Get a user's datasets

**Request Parameters**:

  * *include_hidden* *(only direct auth)*
  * *include_private* *(only direct auth)*

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v1/openplans/datasets/?format=json

**Sample Response**:

    [
      {
        "id": 31,
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/",
        "display_name": "Chicago Bike Share exports",
        "slug": "chicagobikes",

        "keys": {
          "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/keys/"
        },
        "owner": {
          "username": "openplans",
          "id": 7
        },
        "places": {
          "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/places/",
          "length": 1281
        },
        "submissions": [
          {
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/comments/",
            "length": 1166,
            "type": "comments"
          },
          {
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/support/",
            "length": 12389,
            "type": "support"
          }
        ]
      },
      ...
    ]


### POST /api/v1/*:owner*/datasets/

Create a user's datasets

**Authentication**: Basic or session auth *(required)*

**Content type**: application/json

**Sample URL**: http://api.shareabouts.org/api/v1/openplans/datasets/

**Sample Request Data**:

    {
      "slug": "mctesty",
      "display_name": "testy mctest"
    }

**Sample Response**:

    201 CREATED

    {
       "display_name": "testy mctest",
       "id": 90,
       "keys": {
           "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/keys/"
       },
       "owner": {
           "id": 7,
           "username": "openplans"
       },
       "places": {
           "length": 0,
           "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/places/"
       },
       "slug": "mctesty",
       "submissions": [],
       "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/"
    }


### PUT /api/v1/*:owner*/datasets/*:slug*/

Update a user's dataset

**Authentication**: Basic or session auth *(required)*

**Content type**: application/json

**Sample URL**: http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/

**Sample Request Data**:

    {
      "slug": "mctesty",
      "display_name": "testy mctest"
    }

**Sample Response**:

    200 OK

    {
       "display_name": "testy mctest",
       "id": 90,
       "keys": {
           "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/keys/"
       },
       "owner": {
           "id": 7,
           "username": "openplans"
       },
       "places": {
           "length": 0,
           "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/places/"
       },
       "slug": "mctesty",
       "submissions": [],
       "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/"
    }


### DELETE /api/v1/*:owner*/datasets/*:slug*/

Delete a user's dataset

**Authentication**: Basic or session auth *(required)*

**Sample URL**: http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/

**Sample Response**:

    204 NO CONTENT


### GET /api/v1/*:owner*/datasets/*:slug*/

Get the details of a dataset

**Request Parameters**:

  * *include_hidden* *(only direct auth)*
  * *include_private* *(only direct auth)*

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/

**Sample Response**:

      {
        "id": 31,
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/",
        "display_name": "Chicago Bike Share exports",
        "slug": "chicagobikes",

        "keys": {
          "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/keys/"
        },
        "owner": {
          "username": "openplans",
          "id": 7
        },
        "places": {
          "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/places/",
          "length": 1281
        },
        "submissions": [
          {
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/comments/",
            "length": 1166,
            "type": "comments"
          },
          {
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/chicagobikes/support/",
            "length": 12389,
            "type": "support"
          }
        ]
      }

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
