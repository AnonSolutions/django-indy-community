==============
Indy Community
==============

Indy Community is a simple Django framework for building
Hyperledger Indy Agent enabled web applications.
Detailed documentation is in the "docs" directory.

Please see https://github.com/AnonSolutions/django-indy-community


Quick start
-----------

1. Add "indy_community" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'indy_community',
    ]

2. Setup other configuration T.B.D.

3. Include the indy URLconf in your project urls.py like this::

    path('indy/', include('indy_community.urls')),

4. Run `python manage.py migrate` to create the indy models.

5. View detailed documentation in the Docs directory
