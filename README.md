Shareabouts API [![Build Status](https://secure.travis-ci.org/openplans/shareabouts-api.png)](http://travis-ci.org/openplans/shareabouts-api)
===============

The Shareabouts API is the data storage and data management component that
powers the [Shareabouts web application](https://github.com/openplans/shareabouts).
It is a REST API for flexibly storing data about places and an UI for managing
and exporting your data.

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)


Upgrading to Python 3
---------------------
Upgrading is fairly straightforward, except that migrations need to be run twice. First, in settings.py, uncomment the `'social.apps.django_app.default'` line, comment out the `'social_django'` line, and run the `manage.py migrate`.

After that, switch the lines back (comment out the first and uncomment the second) and run `manage.py migrate` again.


Documentation
-------------
All of our documentation is is our `doc` directory. Use it to learn more about:
* [local setup](https://github.com/openplans/shareabouts-api/blob/master/doc/README.md)
* [how to deploy to DotCloud](https://github.com/openplans/shareabouts-api/blob/master/doc/DEPLOY.md)
* [upgrading from an older version](https://github.com/openplans/shareabouts-api/blob/master/doc/UPGRADE.md)

Demo
------------
Please feel free to check out our [staging server](http://sapistaging-civicworks.dotcloud.com/manage/datasets/) to see how it work. Use username `demo-user` and password `demo`

Contributing
------------
In the spirit of [free software](http://www.fsf.org/licensing/essays/free-sw.html), **everyone** is encouraged to help improve this project.

Here are some ways *you* can contribute:

* by joining our developers discussion list: http://groups.google.com/group/shareabouts-dev
* by taking a look at our pipeline in the public tracker: https://www.pivotaltracker.com/projects/398973
* by using alpha, beta, and prerelease versions
* by reporting bugs
* by suggesting new features
* by writing or editing documentation
* by writing specifications
* by writing code (**no patch is too small**: fix typos, add comments, clean up inconsistent whitespace)
* by refactoring code
* by resolving issues
* by reviewing patches

Credits
-------------
Shareabouts is a project of [OpenPlans](http://openplans.org).
