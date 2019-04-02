from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
import yaml
import os

from indy_core.utils import *
from indy_core.models import *
from indy_core.agent_utils import *
from indy_core.registration_utils import *


class Command(BaseCommand):
    help = 'Loads Organizations and optionally creates Credential Definitions'

    def add_arguments(self, parser):
        parser.add_argument('config_file', nargs='+')

    def handle(self, *args, **options):
        schemas = None
        org = None

        # verify that config file exists and we can load yaml
        self.stdout.write("config_file = %s" % str(options['config_file']))
        with open(str(options['config_file'][0]), 'r') as stream:
            try:
                orgs = yaml.load(stream)
            except yaml.YAMLError as exc:
                self.stdout.write(exc)
                raise

            # validate data in yaml file
            for name in orgs:
                org = orgs[name]
                # TODO validation

        # now create orgs (and potentially create cred defs)
        if orgs:
            for name in orgs:
                org = orgs[name]
                first_name = org['first_name']
                last_name = org['last_name']
                email = org['email']
                password = org['password']
                role_name = org['role']

                if "$random" in name:
                    name = name.replace("$random", random_alpha_string(12))
                if "$random" in email:
                    email = email.replace("$random", random_alpha_string(12))

                user = get_user_model().objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password)
                user.groups.add(Group.objects.get(name='User'))
                user.save()

                org_role, created = IndyOrgRole.objects.get_or_create(name=role_name)
                org = org_signup(user, password, name, org_role)
