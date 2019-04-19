# django-indy-community

Django wrapper for a cloud-based Hyperledger Indy Agency for community applications.

This library provides a cloud-based framework for developing Hyperledger Indy Agent applications.  This platform supports agents for both individuals and organizations in a single platform, as well as provides the ability to interact with stand-alone agents.  This library currently supports the VCX agent protocol, however will support interoperable agents as well once a HIPE-compliant python agent is available.

Note that this library is in early development stage.  It s suitable for developing a demonstration or POC but not (yet) for production applications.


## Features

- Easy-to-use wrapper/api around Indy libraries libindy and libvcx
- Supports multiple organizations/roles in a single deployment
- Easy registration process to create new users, organizations and agents
- Admin functions to load schemas, organizations and credential definitions
- Built-in UI, can be extended for business-specific functions (see [demo](https://github.com/AnonSolutions/indy-community-demo))


## Future Features

The following features are planned:

- REST API (and demo application using vue.js)
- Integration of [BC Government Python Agent](https://github.com/bcgov/indy-catalyst)
- "Composer"-like application for generating an application framework
- Additional business demos
- Video tutorials


## Building and Running the Built-in Demo Application

This repository can be run as a stand-alone application to demonstrate Indy and Agent capabilities.  This requires local Indy libraries, as well as a running set of Indy nodes.

There are two ways to accomplish this, to run the demo application:

1. As a fully contained docker build
2. By installing and running all dependencies locally

Both are described (along with docker scripts) [here](./docker).


## Initializing the Demo Application

If you run the Docker-ized version, these steps are part of the application startup.

There are two Admin commands available to "seed" organizations, schemas and credential definitions:

```
python manage.py loads_orgs <orgs yml file>
python manage.py loads_schemas <schemas yml file> <org id>
```

An organization (with an identity on the network) is required to load schemas.  Once schemas are loaded, credential definitions will automatically be created for organizations with matching roles (org role matches schema role).  So, for example, the Docker-ised application runs the following on startup:

```
python manage.py loads_orgs ./trustee-org.yml
python manage.py loads_schemas ./test-schemas.yml 1
python manage.py loads_orgs ./test-orgs.yml
```

Once the organizations, schemas etc. are created, open 2 shells and run the following in each shell (note that this is done automatically within the Docker version):

```
python manage.py runserver
```

```
python manage.py process_tasks
```

You can login to the Django Admin application to inspect the data populated in the application database - https://localhost:8000/admin (admin@mail.com/pass1234)

You can also view the ledger browser (http://localhost:9000/) and inspect the Indy ledger objects created.


## Running a Demo Application Scenario

1. Connect to the application http://localhost:8000/

2a. (Optional) Click on the "Create Organization Account" link at the bottom of the page

2b. (Optional) Enter user and organization information, enter a role matching one of the schema roles

2c. Login as your organization user (or use one of the pre-loaded organizations)

3a. In a separate browser, click on the "Create Individual Account" link at the bottom of the page

3b. Enter user information

3c. Login as your user

You should now have two sessions, one as an organization and one as a user.


## Setting up agent connections

1. Connect to the application http://localhost:8000/

2. As the Organization, click on the Connections tab and then click on "Send Connection Invite".  Enter the user's email (from the previous step) and Submit

3. As the User, click on the Connections tab, there should be a Pending connection. Click on "Respond" and then "Submit"

4. Back to the Organization - click on "Check Status" and then "Submit"

At this point, both parties should have an Active connection to each other.


## Issueing Credentials and Proofs

TBD include additional descriptions, and a link to a video tutorial

