from django.contrib import admin

from .models import *


admin.site.register(IndyUser)
admin.site.register(IndyOrgRole)
admin.site.register(IndyOrganization)
admin.site.register(IndyOrgRelationship)
admin.site.register(IndyWallet)
admin.site.register(IndySchema)
admin.site.register(IndyCredentialDefinition)
admin.site.register(IndyProofRequest)
admin.site.register(AgentConnection)
admin.site.register(AgentConversation)

