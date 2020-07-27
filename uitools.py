'''A wrapper to create nice-looking embed-style messages'''
from discord import Embed, Colour

uiEmoji = {
	'tick'       : [':white_check_mark:', Colour.green()],
	'dollar'     : [':dollar:', Colour.green()],
	'handshake'  : [':handshake:', Colour.green()],

	'gear'       : [':gear:', Colour.lighter_grey()],

	'warning'    : [':warning:', Colour.red()],
	'moneybag'   : [':moneybag:', Colour.gold()],
	'waiting'    : [':hourglass:', Colour.gold()],

	'winner'	 : [':partying_face:', Colour.blue()],
	'loser'	     : [':pensive:', Colour.blue()],
	'push'	     : [':right_facing_fist:', Colour.blue()],
	'blackjack'	 : ['<:poggers:731761300509818882>', Colour.blue()],

	'error'      : [':no_entry:', Colour.red()],
	'raisedhand' : [':raised_hand:', Colour.red()],
}

# A wrapper for creating an dialog box-style embed message.
def dialogBox(messageEmoji, messageTitle, messageContent=False, accentColour='inherit'):
	if not messageContent:
		embed = Embed(
			title = '{emoji}  {title}'.format(emoji=uiEmoji[messageEmoji][0], title=messageTitle),
			colour = uiEmoji[messageEmoji][1]
		)
	else:
		embed = Embed(
			title = '{emoji}  {title}'.format(emoji=uiEmoji[messageEmoji][0], title=messageTitle),
			description = messageContent,
			colour = uiEmoji[messageEmoji][1]
		)
	return embed

# Makes debugging stuff quicker.
def debugMessage(msg):
	return dialogBox('gear', 'Debug output', '`{}`'.format(msg))
