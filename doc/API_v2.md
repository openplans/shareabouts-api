Resources
=========

Datasets
--------

The primary entry point into the API is a dataset. Each dataset has an owner,
and a user can own any number of datasets.

**Fields**:

  * *slug*: the short name for the dataset, used in the url; no user can
    own two datasets with the same slug
  * *display_name*: the human-readable name for the dataset
  * *url*: the URL of the dataset
  * *owner*: an object with the `username` and `id` of the owner
  * *places*: an object with places metadata -- the number (`length`) of
    places, and the `url` of the place collection
  * *submission_sets*: a list of objects with meta data about each submission
    set -- `length`, and `url`
  * *keys*: an object that contains only the URL to the dataset's API keys

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/

Get a user's datasets

**Request Parameters**:

  * include_hidden *(only direct auth)*
  * include_private *(only direct auth)*
  * include_submissions

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets.json

**Sample Response**:

    200 OK

    {
      "metadata": {
        "length": 30,
        "page": 1,
        "next": http://.../api/v2/openplans/datasets.json?page=2,
        "previous": null
      },
      "results": [
        {
          "slug": "chicagobikes",
          "url": "http://.../api/v2/openplans/datasets/chicagobikes/",
          "display_name": "Chicago Bike Share exports",

          "keys": { "url": "http://.../api/v2/openplans/datasets/chicagobikes/keys/" },
          "owner": { "username": "openplans", "url": "http://.../api/v2/openplans/" },
          "places": {
            "url": "http://.../api/v2/openplans/datasets/chicagobikes/places/",
            "length": 1281
          },
          "submission_sets": {
            "comments": {
              "url": "http://.../api/v2/openplans/datasets/chicagobikes/comments/",
              "length": 1166
            },
            "support": {
              "url": "http://.../api/v2/openplans/datasets/chicagobikes/support/",
              "length": 12389
            }
          }
        },
        ...
      ]
    }

------------------------------------------------------------

### POST /api/v2/*:owner*/datasets/

Create a dataset

**Authentication**: Basic or session auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets.json

**Sample Request Data**:

    {
      "slug": "mctesty",
      "display_name": "Testy McTest"
    }

**Sample Response**:

    201 CREATED

    {
      "slug": "mctesty",
      "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/"
      "display_name": "Testy McTest",

      "keys": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/keys/" },
      "owner": { "username": "openplans", "url": "http://api.shareabouts.org/api/v2/openplans/" },
      "places": {
        "length": 0,
        "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/places/"
      },
      "submission_sets": {},
    }

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/*:slug*/

Get a specific dataset

**Request Parameters**:

  * include_hidden *(only direct auth)*
  * include_private *(only direct auth)*
  * include_submissions

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/chicagobikes.json

**Sample Response**:

    200 OK

    {
      "slug": "chicagobikes",
      "url": "http://.../api/v2/openplans/datasets/chicagobikes/",
      "display_name": "Chicago Bike Share exports",

      "keys": { "url": "http://.../api/v2/openplans/datasets/chicagobikes/keys/" },
      "owner": { "username": "openplans", "url": "http://.../api/v2/openplans/" },
      "places": {
        "url": "http://.../api/v2/openplans/datasets/chicagobikes/places/",
        "length": 1281
      },
      "submission_sets": {
        "comments": {
          "url": "http://.../api/v2/openplans/datasets/chicagobikes/comments/",
          "length": 1166
        },
        "support": {
          "url": "http://.../api/v2/openplans/datasets/chicagobikes/support/",
          "length": 12389
        }
      }
    }

------------------------------------------------------------

### PUT /api/v2/*:owner*/datasets/*:slug*/

Update a dataset

**Authentication**: Basic or session auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/oldslug.json

**Sample Request Data**:

    {
      "slug": "mctesty",
      "display_name": "Testy McTest"
    }

**Sample Response**:

    200 OK

    {
      "slug": "mctesty",
      "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/"
      "display_name": "Testy McTest",

      "keys": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/keys/" },
      "owner": { "username": "openplans", "url": "http://api.shareabouts.org/api/v2/openplans/" },
      "places": {
        "length": 0,
        "url": "http://api.shareabouts.org/api/v2/openplans/datasets/mctesty/places/"
      },
      "submission_sets": {},
    }

------------------------------------------------------------

### DELETE /api/v2/*:owner*/datasets/*:slug*

Delete a dataset

**Authentication**: Basic or session auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/mctesty.json

**Sample Request Data**:

    204 NO CONTENT


------------------------------------------------------------

Places
------

Places are the basic unit of a dataset. By default, a place is represented as a
GeoJSON feature.

**Property Fields**:

* *id*:
* *url*:
* *created_datetime*:
* *updated_datetime*:
* *visible*:
* *attachments*:
* *dataset*:
* *submission_sets*:

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/*:slug*/places/

Get all the places in a dataset

**Request Parameters**:

  * include_hidden *(only direct auth)*
  * include_private *(only direct auth)*
  * include_submissions

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places.json

**Sample Response**:

    200 OK

    {
      "metadata": {
        "length": 30,
        "page": 1,
        "next": http://.../api/v2/openplans/datasets/atm_surcharge/places.json?page=2,
        "previous": null
      },
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },

          "properties": {
            "id": 25503,
            "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/",
            "created_datetime": "2013-02-14T01:08:44.893Z",
            "updated_datetime": "2013-02-14T01:08:44.893Z",
            "visible": true,

            "type": "ATM",
            "name": "K-mart",
            "surcharge": "0",
            "submitter_name": "Mjumbe",

            "dataset": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/" },
            "attachments": [],
            "submission_sets": {
              "comments": {
                "length": 1,
                "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/comments/"
              }
            }
          }
        },
        ...
      ]
    }

------------------------------------------------------------

### POST /api/v2/*:owner*/datasets/*:slug*/places/

Create a place

**Authentication**: Basic, session, or key auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places.json

**Sample Request Data**:

    {
      "type": "ATM",
      "name": "K-mart",
      "surcharge": "0",
      "submitter_name": "Mjumbe",
      "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },
      "visible": true
    }

**Sample Response**:

    201 CREATED

    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },

      "properties": {
        "id": 25503,
        "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/",
        "created_datetime": "2013-02-14T01:08:44.893Z",
        "updated_datetime": "2013-02-14T01:08:44.893Z",
        "visible": true,

        "type": "ATM",
        "name": "K-mart",
        "surcharge": "0",
        "submitter_name": "Mjumbe",

        "dataset": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/" },
        "attachments": [],
        "submission_sets": {}
      }
    }

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/*:slug*/places/*:placeid*/

Get a specific place

**Request Parameters**:

  * include_hidden *(only direct auth)*
  * include_private *(only direct auth)*
  * include_submissions

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503.json

**Sample Response**:

    200 OK

    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },

      "properties": {
        "id": 25503,
        "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/",
        "created_datetime": "2013-02-14T01:08:44.893Z",
        "updated_datetime": "2013-02-14T01:08:44.893Z",
        "visible": true,

        "type": "ATM",
        "name": "K-mart",
        "surcharge": "0",
        "submitter_name": "Mjumbe",

        "dataset": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/" },
        "attachments": [],
        "submission_sets": {
          "comments": {
            "length": 1,
            "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/comments/"
          }
        }
      }
    }

------------------------------------------------------------

### PUT /api/v2/*:owner*/datasets/*:slug*/places/*:placeid*/

Update a place

**Authentication**: Basic, session, or key auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503.json

**Sample Request Data**:

    {
      "type": "ATM",
      "name": "K-mart",
      "surcharge": "0.50",
      "submitter_name": "Mjumbe",
      "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },
      "visible": true
    }

**Sample Response**:

    200 OK

    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates: [-73.994711637500004, 40.752499397299999] },

      "properties": {
        "id": 25503,
        "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/",
        "created_datetime": "2013-02-14T01:08:44.893Z",
        "updated_datetime": "2013-02-14T01:08:44.893Z",
        "visible": true,

        "type": "ATM",
        "name": "K-mart",
        "surcharge": "0.50",
        "submitter_name": "Mjumbe",

        "dataset": { "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/" },
        "attachments": [],
        "submission_sets": {
          "comments": {
            "length": 1,
            "url": "http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503/comments/"
          }
        }
      }
    }

------------------------------------------------------------

### DELETE /api/v2/*:owner*/datasets/*:slug*/places/*:placeid*/

Delete a place

**Authentication**: Basic, session, or key auth *(required)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/openplans/datasets/atm_surcharge/places/25503

**Sample Request Data**:

    204 NO CONTENT

------------------------------------------------------------

Submissions
-----------

Submissions are stand-alone objects (key-value pairs) that can be attached to
a place. These could be comments, surveys responses, support/likes, etc. You
can attach multiple submission sets to a place. Submissions are grouped into
sets based on the type of submission.

**Fields**:

* *id*:
* *url*:
* *created_datetime*:
* *updated_datetime*:
* *visible*:
* *attachments*:
* *place*:
* *set*:
* *dataset*:

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/

Get all submissions for a place

**Request Parameters**:

  * *include_invisible* *(only direct auth)*
  * *include_private_data* *(only direct auth)*

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/26836/comments/

**Sample Response**:

    200 OK

    {
      "metadata": {
        "length": 30,
        "page": 1,
        "next": http://api.shareabouts.org/api/v2/openplans/datasets/demo-data/places/26836/comments.json?page=2,
        "previous": null
      },
      "results": [
        {
          "id": 26902,
          "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/26836/comments/26902/",
          "created_datetime": "2013-04-11T16:46:38.662Z",
          "updated_datetime": "2013-04-11T16:46:38.662Z",
          "visible": true,
          "submitter_name": "John",
          "comment": "Agreed.  Caught me a big one just a week ago.",
          "place": {
            "id": 26836,
            "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/26836/"
          },
          "set": {
            "name": "comments",
            "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/26836/comments/"
          },
          "attachments": []
        },
        ...
      ]
    }

------------------------------------------------------------

### POST /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/

Create a submission for a place

**Authentication**: Basic, session, or key auth *(required)*

**Content type**: application/json

**Sample URL**: http://api.shareabouts.org/api/v2/places/29664/comments/

**Sample Request Data**:

    {
        comment: "This is great!"
        submitter_name: "Andy"
        visible: "on"
    }

**Sample Response**:

    201 CREATED

    {
        "id": 29671,
        "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/29671/",
        "updated_datetime": "2013-04-30T15:38:54.449Z",
        "created_datetime": "2013-04-30T15:38:54.449Z",
        "visible": true,
        "submitter_name": "Andy",
        "comment": "This is great!",
        "place": {
            "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/",
            "id": 29664
        },
        "set": {
          "name": "comments",
          "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/"
        },
        "attachments": []
    }

------------------------------------------------------------

### GET /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/*:submission_id*/

Get a particular submission

**Request Parameters**:

  * *include_invisible* *(only direct auth)*
  * *include_private_data* *(only direct auth)*

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/places/29664/comments/29671/

**Sample Response**:

    200 OK

    {
        "id": 29671,
        "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/29671/",
        "updated_datetime": "2013-04-30T15:38:54.449Z",
        "created_datetime": "2013-04-30T15:40:16.145Z",
        "visible": true,
        "submitter_name": "Andy",
        "comment": "This is REALLY great!",
        "place": {
            "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/",
            "id": 29664
        },
        "set": {
          "name": "comments",
          "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/"
        },
        "attachments": []
    }

------------------------------------------------------------

### PUT /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/*:submission_id*/

Update a submission for a place of a specific type

**Authentication**: Basic, session, or key auth *(required)*

**Content type**: application/json

**Sample URL**: http://api.shareabouts.org/api/v2/places/29664/comments/29671/

**Sample Request Data**:

    {
        comment: "This is REALLY great."
        submitter_name: "Andy"
        visible: "on"
    }

**Sample Response**:

    200 OK

    {
        "id": 29671,
        "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/29671/",
        "updated_datetime": "2013-04-30T15:38:54.449Z",
        "created_datetime": "2013-04-30T15:40:16.145Z",
        "visible": true,
        "submitter_name": "Andy",
        "comment": "This is REALLY great!",
        "place": {
            "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/",
            "id": 29664
        },
        "set": {
          "name": "comments",
          "url": "http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/places/29664/comments/"
        },
        "attachments": []
    }

------------------------------------------------------------

### DELETE /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/*:submission_id*/

Delete a submission

**Authentication**: Basic, session, or key auth *(required)*

**Sample URL**: http://api.shareabouts.org/api/v2/places/29664/comments/29671/

**Sample Response**:

    204 NO CONTENT


------------------------------------------------------------

Activity
--------

### GET /api/v2/*:owner*/datasets/*:ds-slug*/activity/

Get the activity for a dataset

**Request Parameters**:

  * `before` -- The id of the latest activity to return.  The
                most recent results with the given id or lower will be
                returned.
  * `after` -- The id of the earliest activity to return.  The
               most recent results with ids higher than *but not including*
               the given time will be returned.
  * `limit` -- The maximum number of results to be returned.
  * `visible` -- Set to `all` to return activity for both visible and
                 invisible places.

**Authentication**: Basic, session, or key auth *(optional)*

**Response Formats**: JSON (default), CSV, HTML, XML

**Sample URL**: http://api.shareabouts.org/api/v2/demo-user/datasets/demo-data/activity/

**Sample Response**:

    200 OK

    [
        {
            "id": 159985,
            "place_id": 29673,
            "action": "create",

            "target_type": "support"
            "target": {
                "created_datetime": "2013-04-30T19:47:21.101Z",
                "updated_datetime": "2013-04-30T19:47:21.101Z",
                "id": 29674,
                "submitter_name": "",
                "user_token": "session:e574c75e35d2e418a5de663b4b0c0691"
            },
        },
        ...
    ]


Attachments
-----------

Attachments are file data that can be attached to a place or a submission.
Attachment files are stored as resources external to the Shareabouts API, but
can be uploaded through the API.

### POST

    /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/attachments
    /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/*:submission_id*/attachments

Create a new attachment for a place or submission

**Authentication**

Basic, session, or key auth *(required)*

**Request Data**

Multipart form data with two fields:

  * `name`: The attachment's name -- should be unique within the place.
  * `file`: The attachment's file data.

**Sample URL**

    http://api.shareabouts.org/api/v2/openplans/datasets/patiosoftheworld/places/29664/attachments
    http://api.shareabouts.org/api/v2/openplans/datasets/patiosoftheworld/places/29664/comments/123/attachments

**Sample Usage**

In Javascript (with jQuery), this can be done like:

    var data = new FormData(),
        fileField = document.getElementById('patio-form');
    data.append('name', 'patio-photo')
    data.append('file', fileField.files[0])

    jQuery.ajax({
      url: 'http://api.shareabouts.org/api/v2/openplans/patiosoftheworld/places/29664/attachments',
      type: 'POST',
      data: data,

      contentType: false,
      processData: false
    });

Or, in Python, with requests:

    import requests
    requests.request(
        'POST',
        'http://api.shareabouts.org/api/v2/openplans/patiosoftheworld/places/29664/attachments/',
        data={'name': 'patio-photo'}
        files={'file': open('filename.jpg')}
    )

**Sample Response**

    200 OK
    {
      "created_datetime": "2013-09-16T14:33:11.043Z",
      "updated_datetime": "2013-09-16T14:33:11.043Z",
      "name": "patio-photo",
      "url": "http://patiosoftheworld.s3.amazon.com/patiomap-attachments/pDf3r4.jpg"
    }

### GET List

    /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/attachments
    /api/v2/*:owner*/datasets/*:slug*/places/*:place_id*/*:submission_set_name*/*:submission_id*/attachments

Get all the attachments for a place or submission

**Authentication**

Basic, session, or key auth *(optional)*

**Response Formats**

JSON (default), CSV, HTML, XML

**Sample URL**

    http://api.shareabouts.org/api/v2/openplans/datasets/patiosoftheworld/places/29664/attachments
    http://api.shareabouts.org/api/v2/openplans/datasets/patiosoftheworld/places/29664/comments/123/attachments

**Sample Response**

    200 OK
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "created_datetime": "2013-09-16T14:33:11.043Z",
                "updated_datetime": "2013-09-16T14:33:11.043Z",
                "file": "http://example.com/attachments/OHc2QOR-milk.jpg",
                "name": "milk.jpg"
            }
        ]
    }

------------------------------------------------------------

