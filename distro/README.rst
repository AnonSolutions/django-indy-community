==============
Indy Community
==============

Indy Community is a simple Django framework for building
Hyperledger Indy Agent enabled web applications.
Detailed documentation is in the "docs" directory.

Please see https://github.com/AnonSolutions/django-indy-community for detailed docmentation


Quick start
-----------

You can find a basic Indy Community application here https://github.com/AnonSolutions/indy-community-demo

To add indy_community to your own django application:

1. Copy the requirements.txt file into your application directory and install requirements

2. Add "indy_community" to your INSTALLED_APPS setting like this:

.. code-block:: python

        INSTALLED_APPS = [
            # this should go first
            'indy_community.apps.IndyCoreConfig',
            ...
        ]

3. Add the following Indy configuration settings (this is for a local install):

.. code-block:: python

        import platform

        def file_ext():
            if platform.system() == 'Linux':
                return '.so'
            elif platform.system() == 'Darwin':
                return '.dylib'
            elif platform.system() == 'Windows':
                return '.dll'
            else:
                return '.so'

        INDY_CONFIG = {
            'storage_dll': 'libindystrgpostgres' + file_ext(),
            'storage_entrypoint': 'postgresstorage_init',
            'payment_dll': 'libnullpay' + file_ext(),
            'payment_entrypoint': 'nullpay_init',
            'wallet_config': {'id': '', 'storage_type': 'postgres_storage'},
            'wallet_credentials': {'key': ''},
            'storage_config': {'url': 'localhost:5432'},
            'storage_credentials': {'account': 'postgres', 'password': 'mysecretpassword', 'admin_account': 'postgres', 'admin_password': 'mysecretpassword'},
            'vcx_agency_url': 'http://localhost:8080',
            'vcx_agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
            'vcx_agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
            'vcx_payment_method': 'null',
            'vcx_enterprise_seed': '000000000000000000000000Trustee1',
            'vcx_institution_seed': '00000000000000000000000000000000',
            'vcx_genesis_path': '/tmp/atria-genesis.txt',
            'register_dids': True,
            'ledger_url': 'http://localhost:9000',
        }

4. Configure background tasks:

.. code-block:: python

        INSTALLED_APPS = [
            ...
            'background_task',
            ...
        ]

        BACKGROUND_TASK_RUN_ASYNC = False
        BACKGROUND_TASK_ASYNC_THREADS = 1
        MAX_ATTEMPTS = 1

5. Ensure your local templates are loaded first:

.. code-block:: python

        TEMPLATES = [
            {
                ...
                'DIRS': [
                    os.path.join(BASE_DIR, '<your app>/templates'),
                ],
                ...
            },
        ]

6. Override User, Organization and Relationship models, if you have your own subclass of these models:

.. code-block:: python

        AUTH_USER_MODEL = 'indy_community.IndyUser'
        INDY_ORGANIZATION_MODEL = 'indy_community.IndyOrganization'
        INDY_ORG_RELATION_MODEL = 'indy_community.IndyOrgRelationship'

7. Include the indy URLconf in your project urls.py like this:

.. code-block:: python

        path('indy/', include('indy_community.urls')),

8. Ensure you have all pre-requisites running, as per django-indy-community docs

9. Run `python manage.py migrate` to create the indy models.

10. Run `python manage.py runserver` and connect to http://localhost:8000/indy`

You can customize the UI and add event handling for VCX Connection and Messaging events.  See the demos in
https://github.com/AnonSolutions/indy-community-demo for examples of how to do this.

View detailed documentation in the Docs directory (https://github.com/AnonSolutions/django-indy-community)

