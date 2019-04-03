import json
import datetime
import pytz

from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

from background_task import background

from indy.error import ErrorCode, IndyError

from .models import IndySession, IndyWallet, AgentConnection, AgentConversation
from .agent_utils import check_connection_status, handle_inbound_messages, poll_message_conversations

AGENT_POLL_INTERVAL = 5


@background(schedule=AGENT_POLL_INTERVAL)
def agent_background_task(message, user_id, session_key, org_id=None):
    # check if user/wallet has a valid session
    user = get_user_model().objects.filter(id=user_id).first()
    try:
        session = IndySession.objects.get(user=user, session_id=session_key)
    except:
        raise Exception("No Indy Session found for {} {}".format(user.email, session_key))

    print("Found session {}  for user {} wallet {}".format(session.id, user.email, session.wallet_name))
    if session.session.expire_date < timezone.get_current_timezone().localize(datetime.datetime.now()):
        raise Exception("Django Session timed out for {} {}".format(user.email, session.wallet_name))

    if session.wallet_name is not None:
        wallet = IndyWallet.objects.get(wallet_name=session.wallet_name)

        # check for outstanding connections and poll status
        connections = AgentConnection.objects.filter(wallet=wallet, status='Sent').all()

        # if (anything to do) initialize VCX agent and do all our updates
        # TODO (for now each request re-initializes VCX)
        for connection in connections:
            # validate connection and get the updated status
            try:
                upd_connection = check_connection_status(wallet, connection)
            except IndyError as e:
                print(" >>> Failed to update connection request for", session.wallet_name, connection.id, connection.partner_name)
                raise e

        # check for outstanding connections and poll status
        connections = AgentConnection.objects.filter(wallet=wallet, status='Active').all()
        for connection in connections:
            # check for outstanding, un-received messages - add to outstanding conversations
            try:
                #if connection.connection_type == 'Inbound':
                msg_count = handle_inbound_messages(wallet, connection)
            except IndyError as e:
                print(" >>> Failed to handle inbound messages for", session.wallet_name, connection.id, connection.partner_name)
                raise e

            # check status of any in-flight conversations (send/receive credential or request/provide proof)
            try:
                polled_count = poll_message_conversations(wallet, connection)
            except IndyError as e:
                print(" >>> Failed to poll conversations for", session.wallet_name, connection.id, connection.partner_name)
                raise e

