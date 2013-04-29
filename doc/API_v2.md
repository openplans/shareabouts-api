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

Create a dataset

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



Attachments
-----------

You can attach files to places and submissions.

  * **Method**: POST

    **URL**: /api/v2/&lt;owner&gt;/datasets/&lt;dataset&gt;/places/&lt;place&gt;/attachments/

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
