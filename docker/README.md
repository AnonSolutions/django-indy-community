# Running using Docker

1. Check out the project https://github.com/bcgov/von-network

2. In the von-network directory, run:

```
./manage build
./manage start
```

This starts a 4-node Indy network, plus a ledger browser (on http://localhost:9000)

3. Check out this project (https://github.com/anonsolutions/django-indy-community)

4. In the docker directory, run:

```
./base-image
```

This builds a base docker image with all the Indy SDK binaries and Python libraries

4. In the same directory, run:

```
./manage start
```

This starts the postgres database (for wallets), cloud agent (for VCX) plus the Demo application.

Connect to the application at http://localhost:8000, or http://localhost:8000/admin (for admin functions)

Note that the django application directory (indy_community) is mounted by the docker container, so any file changes will be automatically loaded by the application.

