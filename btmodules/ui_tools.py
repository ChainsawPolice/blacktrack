'''A wrapper to create nice-looking embed-style messages'''
from discord import Embed, Colour

uiEmoji = {
	'tick'       : [':white_check_mark:', Colour.green()],
	'dollar'     : [':dollar:', Colour.green()],
	'handshake'  : [':handshake:', Colour.green()],

	'gear'       : [':gear:', Colour.lighter_grey()],

	'moneybag'   : [':moneybag:', Colour.gold()],
	'waiting'    : [':hourglass:', Colour.gold()],
	'raisedhand' : [':raised_hand:', Colour.gold()],

	'winner'	 : [':partying_face:', Colour.blue()],
	'loser'	     : [':pensive:', Colour.blue()],
	'push'	     : [':right_facing_fist:', Colour.blue()],
	'blackjack'	 : ['<:poggers:731761300509818882>', Colour.blue()],
	'die'        : [':game_die:', Colour.blue()],

	'warning'    : [':warning:', Colour.red()],
	'error'      : [':no_entry:', Colour.red()],
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
