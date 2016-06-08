Once you have a [Shareabouts map](https://github.com/openplans/shareabouts/blob/master/README.md#a-short-guide-to-setting-up-shareabouts) collecting data, you can explore the data via the Django admin interface, and via the web-based RESTful API browser.



## Viewing data via the Django admin interface

Shareabouts data is accessible via the regular Django interface, at

        https://SERVER/admin/

e.g.

        http://data.shareabouts.org/admin/

The trailing slash after `admin` is necessary, don't forget it.

### What can I do with the Django admin interface?

Using the Django interface, you can
* create new datasets and API keys
* view places by date
* view places in a particular dataset
* hide or show places with the Visibility checkbox in list view
* edit place data via the json blob editor

You cannot
* download data in a csv
* easily browse through data



## Viewing and downloading data via the API

You can explore your datasets here:

        https://SERVER/api/v2/USER/datasets/

e.g.

        http://data.shareabouts.org/api/v2/openplans/datasets

At that URL, you'll see a list of datasets, with links to each dataset's places, supports, and surveys (which are comments).

### Where's my private data?

Private data in Shareabouts can only be accessed by an authenticated user.
If you have fields prefixed with `private-` in your config, those fields aren't
accessible unless you log in to the Django admin interface before using the API browser.

Use your admin account for `https://SERVER/admin/` (e.g. `http://data.shareabouts.org/admin/`)
to add yourself as a superuser OR to set a password for the dataset owner.

Then, log in via `https://SERVER/admin/`, then use the API browser in another tab. Private data shows up if you include `?include_private` in the url, e.g.

       http://data.shareabouts.org/api/v2/openplans/datasets/test-data/places?include_private

### Downloading snapshots

Data from the API can be paginated (using the `page_size` and `page` parameters), but it's tedious to assemble files offline, and if you make the page size too large, the page won't get generated before the server times out.

Instead, use the `/snapshots` endpoint. This will queue up the process of generating an entire file on request, which you can download once it has been created.

To generate a snapshot, visit `server/api/v2/user/datasets/datasets/places/snapshots?new` e.g.

          https://data.shareabouts.org/api/v2/openplans/datasets/test-data/places/snapshots?new

Swap `surveys` for `places` to download comments.

If you are logged in as the dataset owner or a server administrator you can download a snapshot with private data included as well by including the `include_private` querystring parameter, i.e. `server/api/v2/user/datasets/datasets/places/snapshots?include_private&new`

Refresh the provided link, if the file isn't ready you'll see 'You can download the data at the given URL when it is done being generated'.

Once you have the download link, you most likely want it as a csv. Add `.csv` to the end of the url, and then do a "Save Page As" from your browser. E.g.
* generate a snapshot
* load the provided URL, like `https://data.shareabouts.org/api/v2/openplans/datasets/test-data/places/snapshots/dac284a6-734a-0b31314e3505`
* reload it with `.csv` on the end, `https://data.shareabouts.org/api/v2/openplans/datasets/test-data/places/snapshots/dac284a6-734a-0b31314e3505.csv`
* save the file (copying it out to a file will give you something with weird line breaks)



## Getting data via the Shareabouts CLI tools

You can use the separate [Shareabouts command line tools](https://github.com/openplans/shareabouts-cli-tools) to import and export data from a Shareabouts dataset. These python scripts make it easy to generate nightly reports, upload polygons, get custom CSV exports, and more.



## Transferring data from one API to another

1. **Create a new dataset with keys/origins the same as the old dataset.**

   This can either be done through the API at */api/v2/<owner>/datasets*, or
   through the Django admin interface at */admin/sa_api_v2/dataset/add/*. You
   will have to set the keys and origins through the Django admin interface.

2. **Switch the dataset root URL to the new dataset.**

   You can do this through with the Heroku command line client:

    heroku config:set DATASET_ROOT=<path-to-new-dataset>

   You can also now do this through Heroku's web dashboard interface. Navigate
   to the **Settings** tab for your app, and find the **Reveal Config Vars**
   button. Click **Edit** to change a value.

3. **Make a snapshot of the old dataset.**

   The places snapshot should include all private data, invisible data, and
   submissions on each place. First, navigate to
   */api/v2/<old-owner>/datasets/<old-slug>/places/snapshots?include_private&include_invisible&include_submissions&new*.
   Next, remove the *new* parameter from the URL and wait until the snapshot
   is ready (until the status is `'success'`). When it is done, copy the given
   URL.

4. **Load the old data into the new dataset.**

   Navigate to */api/v2/<owner>/datasets/<slug>* and paste the URL from step
   3 in to the *Load from URL* field. Click **PUT** and the data should begin
   to load. You won't see the results until the data has completed. It may
   take a while. **Note** that it will note all data as new data; i.e., if you
   do step #4 twice, it may load twice as many points as you expect. So **do
   not retry** unless you know something went wrong. You can check whether
   something went wrong by inspecting the server logs (not ideal, I know).
