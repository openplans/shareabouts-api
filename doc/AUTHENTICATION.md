Authentication
==============

There are several authentication methods available within the Shareabouts API, and they all allow you to do different things. Each is appropriate for different situations.


### Types of authentication

You can authenticate users directly, as dataset owner or a content submitter. When authenticating a user directly as a dataset owner through any of these methods, you give the user full permission to modify any aspect of their datasets through the API (but only for the datasets that that user owns).

To authenticate a user directly, you can use:

* Basic Authentication, e.g.:

      curl http://myuser:password@<your-host>/api/v2/myuser/datasets

* 3rd Party Authentication through Facebook or Twitter (see below)
* OAuth2

You can also authenticate a client application on behalf of a dataset owner. These authentication methods have more limited permissions to modify a dataset's data. You might want to use these when allowing users to contribute data anonymously without giving unrestricted access to write to a dataset. These methods are:

* Key authentication, e.g.:

      curl http://myuser:password@<your-host>/api/v2/myuser/datasets \
           -H "X-Shareabouts-Key: xxxxxxxxxxxxxxxxx"

* Origin authentication (for CORS requests), e.g.:

      curl http://myuser:password@<your-host>/api/v2/myuser/datasets \
           -H "Origin: www.myappdomain.com"


### The command line

When testing your dataset through the command line (or through a simple script) basic auth (if you are comfortable using a username/password) or api key auth are usually easiest.


Authenticating Users with Facebook or Twitter
---------------------------------------------

When you build an application on top of the Shareabouts API, users do not log in to your specific app with Facebook or Twitter; instead they log in to the Shareabouts API server. The API server takes care of the communication between Facebook and Twitter. Just point your users at `https://<your-host>/api/v2/users/login/facebook/` or `https://<your-host>/api/v2/users/login/twitter/`, respectively.

By default, the API server will send the user back to the same page of the originating app after they have authenticated. If there is a specific page you want the user redirected to, use the `next` parameter, e.g.:

    https://<your-host>/api/v2/users/login/twitter/?next=/profile

If there is a special page you would like to be shown if the user declines permission, or any other error occurs, use the `error_next` parameter, e.g.:

    https://<your-host>/api/v2/users/login/twitter/?next=/profile&error_next=/login-failed


Accessing the Current User
--------------------------

You can access the current user's information at `https://<your-host>/api/v2/users/current`. If no user is logged in this will simply return `null`. It may be useful to use this through JSON-P if you require user information when your page loads. For example:

    <script>
      var setUser = function(data) {
        if (data) {
          $('#user-info').html(
          	'<img src="' + data['avatar_url'] + '"> | ' +
          	'<a href="https://<your-host>/api/v2/users/logout">Logout</a>');
        }
      };
    </script>
    <script src="https://<your-host>/api/v2/users/current?callback=setUser"></script>

This endpoint provides:

  * `name`
  * `avatar_url`
  * `id`
  * `username`

CORS is enabled on this endpoint as well, so you can also access the information via AJAX. For AJAX requests, be sure to include the `withCredentials` XHR flag, e.g.:

    function initUser() {
      $.ajax({
        url: 'https://<your-host>/api/v2/users/current',
        xhrFields: {
          withCredentials: true
        },
        success: function(userData) {
          if (userData) console.log(userData);
          else console.log('No user data');
        }
      });
    };
