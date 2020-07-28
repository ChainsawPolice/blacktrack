''' Commonly-used utilities shared among modules '''
from btmodules.global_constants import dealerRoleID
import btmodules.db_utils

# Formats floats as currency.
def asMoney(value):
	if float(value).is_integer():
		return "${:,.0f}".format(value)
	else:
		return "${:,.2f}".format(value)

# Check if the user is a dealer.
# TODO: Clean this up. there's definitely a way to shorten this - there _has_ to be.
def isDealer(userObject):
	listOfRoleIDs = []
	for role in userObject.roles:
		if role.id == dealerRoleID:
			return True
	return False

# Get a user's avatar URL
def getAvatarURL(ctx,userID):
	for thisMember in ctx.guild.members:
		if int(thisMember.id) == int(userID):
			return str(thisMember.avatar_url_as(format='png', static_format='png', size=1024))
	else:
		return 'https://cdn.discordapp.com/avatars/735083076165828628/b45f1aa524c3c5c6638a4dfacfdf43d2.png?size=1024'

# Convert a user mention string to a user ID.
def convertMentionToID(userMention):
	return int(userMention[3:-1])
