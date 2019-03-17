
from .models import *
from .indy_utils import *
from .wallet_utils import *
from .agent_utils import *


def user_provision(user, raw_password):
    """
    Create a new user wallet and associate with the user
    """
    wallet_name = get_user_wallet_name(user.email)
    res = create_wallet(wallet_name, raw_password)
    if res != 0:
        raise Exception("Error wallet create failed: " + str(res))

    # provision as an agent wallet (errors will raise exceptions)
    config = initialize_and_provision_vcx(wallet_name, raw_password, user.email)

    # save everything to our database
    wallet = IndyWallet.objects.create(wallet_name=wallet_name, wallet_config = config)
    wallet.save()
    user.wallet = wallet
    user.save()


def org_provision(org, raw_password, org_role=''):
    """
    Create a new org wallet and associate to the org
    """
    wallet_name = get_org_wallet_name(org.org_name)
    res = create_wallet(wallet_name, raw_password)
    if res != 0:
        raise Exception("Error wallet create failed: " + str(res))

    # create a did for this org
    did_seed = calc_wallet_seed(wallet_name)
    if org_role != "Trustee":
        create_and_register_did(wallet_name, org_role)

    # provision as an agent wallet (errors will raise exceptions)
    config = initialize_and_provision_vcx(wallet_name, raw_password, org.org_name, did_seed=did_seed, org_role=org_role)

    # save everything to our database
    wallet = IndyWallet.objects.create(wallet_name=wallet_name, wallet_config = config)
    wallet.save()
    org.wallet = wallet
    org.save()


def org_signup(user, raw_password, org_name, org_role=''):
    """
    Helper method to create and provision a new org, and associate to the current user
    """
    org = IndyOrganization.objects.create(org_name=org_name)

    org_provision(org, raw_password, org_role)

    # associate the user with the org
    relation = IndyOrgRelationship.objects.create(org=org, user=user)
    relation.save()

    return org

