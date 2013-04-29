Resources
=========

Datasets
--------

The primary entry point into the API is a dataset. Each dataset has an owner,
and a user can own any number of datasets.

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

    {
      "metadata": {
        "length": 2,
        "page": 1,
        "next": null,
        "previous": null
      },
      "results": [
        {
          "slug": "atm_surcharge",
          "url": "http://.../api/v2/openplans/datasets/atm_surcharge/",
          "display_name": "ATM Surcharge",

          "keys": { "url": "http://.../api/v2/openplans/datasets/atm_surcharge/keys/" },
          "owner": { "username": "openplans", "url": "http://.../api/v2/openplans/" },
          "places": {
            "url": "http://.../api/v2/openplans/datasets/atm_surcharge/places/",
            "length": 31
          },
          "submission_sets": {
            "comments": {
              "length": 13,
              "url": "http://.../api/v2/openplans/datasets/atm_surcharge/comments/"
            }
          }
        },
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

**201 Created**
    
    {
      "slug": "mctesty", 
      "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/"
      "display_name": "Testy McTest", 

      "keys": { "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/keys/" }, 
      "owner": { "username": "openplans" }, 
      "places": {
        "length": 0, 
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/mctesty/places/"
      }, 
      "submission_sets": {}, 
    }

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
