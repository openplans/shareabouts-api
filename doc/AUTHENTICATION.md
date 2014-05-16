Authenticating Users with Facebook or Twitter
=============================================

Users do not log in to your specific app with Facebook or Twitter; instead they log in to the Shareabouts API server. The API server takes care of handling the communication between Facebook and Twitter. Just point your users at `http://data.shareabouts.org/api/v2/users/login/facebook/` or `http://data.shareabouts.org/api/v2/users/login/twitter/`, respectively.

By default, the API server will send the user back to the same page of the originating app after they have authenticated. If there is a specific page you want the user redirected to, use the `next` parameter, e.g.:

    http://data.shareabouts.org/api/v2/users/login/twitter/?next=/profile

If there is a special page you would like to be shown if the user declines permission, or any other error occurs, use the `error_next` parameter, e.g.:

    http://data.shareabouts.org/api/v2/users/login/twitter/?next=/profile&error_next=/login-failed


Accessing the Current User
--------------------------

You can access the current user's information at `http://data.shareabouts.org/api/v2/users/current`. If no user is logged in this will simply return `null`. It may be useful to use this through JSON-P if you require user information when your page loads. For example:

    <script>
      var setUser = function(data) {
        if (data) {
          $('#user-info').html(
          	'<img src="' + data['avatar_url'] + '"> | ' +
          	'<a href="http://data.shareabouts.org/api/v2/users/logout">Logout</a>');
        }
      };
    </script>
    <script src="http://data.shareabouts.org/api/v2/users/current?callback=setUser"></script>

This endpoint provides:

  * `name`
  * `avatar_url`
  * `id`
  * `username`

CORS is enabled on this endpoint as well, so you can also access the information via AJAX. For AJAX requests, be sure to include the `withCredentials` XHR flag, e.g.:

    function initUser() {
      $.ajax({
        url: 'http://data.shareabouts.org/api/v2/users/current',
        xhrFields: {
          withCredentials: true
        },
        success: function(userData) {
          if (userData) console.log(userData);
          else console.log('No user data');
        }
      });
    };
