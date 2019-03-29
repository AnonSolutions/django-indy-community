# django-indy-agent

Django wrapper for a cloud-based Hyperledger Indy Agency for community applications.

This library provides a cloud-based framework for developing Hyperledger Indy agent applications.  This platform supports agents for both individuals and organizations in a single platform, as well as provides the ability to interact with stand-alone agents.  This library currently supports the VCX agent protocol, however will support interoperable agents as well once a HIPE-compliant python agent is available.

Note that this library is in early development stage.  It s suitable for developing a demonstration or POC but not (yet) for production applications.


## Building and Running the Demo Application

This application requires local Indy libraries, as well as a running set of Indy nodes.

There are two ways to accomplish this, to run the demo application:

1. As a fully contained docker build
2. By installing and running all dependencies locally

Both are described (along with docker scripts) [here](./docker).


## Running a Demo Application Scenario

1. Connect to the application http://localhost:8000/

2. Click on the "Create Organization Account" link at the bottom of the page

3. Enter user and organization information, enter the role as "Trustee"

4. In a separate shell, run the following to load schemas and credential definitions:

```bash
cd django-indy-community/indy_community
python manage.py loads_schemas ../test-schemas.yml 1 --cred_defs
```

5. Click on the "Create Organization Account" link at the bottom of the page (again)

6. Enter a second user and organization information, enter the role as "Test" (this will create Credential Definitions for this organization)

7. Login to the admin interface (http://localhost:8000/admin/) and inspect the database objects that are created

8. View the ledger browser (http://localhost:9000/) and inspect ledger objects created


## Setting up agent connections

1. Connect to the application http://localhost:8000/

2. Click on the "Create Individual Account" link at the bottom of the page

3. Enter user information and Submit (remember the email address)

4. Login as the user

5. In a separate browser, login as the Organization created above

6. As the Organization, click on the Connections tab and then click on "Send Connection Invite".  Enter the user's email (from step 3) and Submit

7. As the User, click on the Connections tab, there should be a Pending connection. Click on "Respond" and then "Submit"

8. Back to the Organization - click on "Check Status" and then "Submit"

At this point, both parties should have an Active connection to each other.


