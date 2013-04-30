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
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/", 
            "created_datetime": "2013-02-14T01:08:44.893Z", 
            "updated_datetime": "2013-02-14T01:08:44.893Z", 
            "visible": true,
            
            "type": "ATM", 
            "name": "K-mart", 
            "surcharge": "0", 
            "submitter_name": "Mjumbe", 

            "dataset": { "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/" }, 
            "attachments": [], 
            "submission_sets": {
              "comments": {
                "length": 1, 
                "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/comments/"
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
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/", 
        "created_datetime": "2013-02-14T01:08:44.893Z", 
        "updated_datetime": "2013-02-14T01:08:44.893Z", 
        "visible": true,
        
        "type": "ATM", 
        "name": "K-mart", 
        "surcharge": "0", 
        "submitter_name": "Mjumbe", 

        "dataset": { "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/" }, 
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
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/", 
        "created_datetime": "2013-02-14T01:08:44.893Z", 
        "updated_datetime": "2013-02-14T01:08:44.893Z", 
        "visible": true,
        
        "type": "ATM", 
        "name": "K-mart", 
        "surcharge": "0", 
        "submitter_name": "Mjumbe", 

        "dataset": { "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/" }, 
        "attachments": [], 
        "submission_sets": {
          "comments": {
            "length": 1, 
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/comments/"
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
        "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/", 
        "created_datetime": "2013-02-14T01:08:44.893Z", 
        "updated_datetime": "2013-02-14T01:08:44.893Z", 
        "visible": true,
        
        "type": "ATM", 
        "name": "K-mart", 
        "surcharge": "0.50", 
        "submitter_name": "Mjumbe", 

        "dataset": { "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/" }, 
        "attachments": [], 
        "submission_sets": {
          "comments": {
            "length": 1, 
            "url": "http://api.shareabouts.org/api/v1/openplans/datasets/atm_surcharge/places/25503/comments/"
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
