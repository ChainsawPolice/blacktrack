import discord
import json
import pprint
import blacktrack_token
from discord.ext import commands
from active_alchemy import ActiveAlchemy

# Instantiate the bot's Discord session.
client = commands.Bot(command_prefix='$')

# Global variables and functions
wallets = {}
currentBets = {} # A dict containing user IDs and their corresponding bet.
betsOpen = False # Whether or not the table is accepting new bets.
channeltoWatch = 735381840835379259
deleteUserMessages = False
uiEmoji = {
	'tick'       : [':white_check_mark:', discord.Colour.green()],
	'dollar'     : [':dollar:', discord.Colour.green()],
	'handshake'  : [':handshake:', discord.Colour.green()],

	'gear'       : [':gear:', discord.Colour.lighter_grey()],

	'warning'    : [':warning:', discord.Colour.red()],
	'moneybag'   : [':moneybag:', discord.Colour.gold()],
	'waiting'    : [':hourglass:', discord.Colour.gold()],

	'winner'	 : [':partying_face:', discord.Colour.blue()],
	'loser'	     : [':pensive:', discord.Colour.blue()],
	'push'	     : [':right_facing_fist:', discord.Colour.blue()],
	'blackjack'	 : ['<:poggers:731761300509818882>', discord.Colour.blue()],

	'error'      : [':no_entry:', discord.Colour.red()],
	'raisedhand' : [':raised_hand:', discord.Colour.red()],
}
defaultWalletAmount = float(200)

# -------------------------------------------------------------------------------------------- #
# Set up database connection
db = ActiveAlchemy('sqlite:///blacktrack.db')
class User(db.Model):
	dc_uniqueid      = db.Column(db.String(100))
	dc_username      = db.Column(db.String(100))
	real_name        = db.Column(db.String(100))
	wallet           = db.Column(db.Integer, default=defaultWalletAmount)
	total_bets       = db.Column(db.Integer, default=0)
	total_wins       = db.Column(db.Integer, default=0)
	total_losses     = db.Column(db.Integer, default=0)
	total_buyins     = db.Column(db.Integer, default=0)
	total_winnings   = db.Column(db.Integer, default=0)

class Bets(db.Model):
	bet_user_id = db.Column(db.String(25))
	bet_amount = db.Column(db.Integer)
# -------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------- #
#Useful functions

# Check if the user is a dealer.
# TODO: Clean this up. there's definitely a way to shorten this - there _has_ to be.
def isDealer(userObject):
	listOfRoleIDs = []
	for role in userObject.roles:
		listOfRoleIDs.append(role.id)
	if 735351625899573341 in listOfRoleIDs:
		return True
	else:
		return False

# Run a query to see if a user exists in the database already. Returns the query object if found, False if not.
# TODO: Clean up this god-forgotten mess of sellotaped-together code.
def userInDatabase(userID):
	for thisUser in User.query().order_by(User.updated_at.desc()).filter(User.dc_uniqueid == int(userID)):
		return thisUser
	return False

# A wrapper for creating an dialog box-style embed message.
def dialogBox(messageEmoji, messageTitle, messageContent=False, accentColour='inherit'):
	if not messageContent:
		embed = discord.Embed(
			title = '{emoji}  {title}'.format(emoji=uiEmoji[messageEmoji][0], title=messageTitle),
			colour = uiEmoji[messageEmoji][1]
		)
	else:
		embed = discord.Embed(
			title = '{emoji}  {title}'.format(emoji=uiEmoji[messageEmoji][0], title=messageTitle),
			description = messageContent,
			colour = uiEmoji[messageEmoji][1]
		)
	return embed

# Makes debugging stuff quicker.
def debugMessage(msg):
	return dialogBox('gear', 'Debug output', '`{}`'.format(msg))

# Work smarter, not harder.
def asMoney(value):
	if float(value).is_integer():
		return "${:,.0f}".format(value)
	else:
		return "${:,.2f}".format(value)

# Pay out a user
def payUserOut(ctx,userMentionString, payoutRatio,winState='push'):
	dbUser = userInDatabase(userMentionString)

	if userMentionString not in currentBets:
		return dialogBox('warning', 'No bets currently standing for {user}.', 'They may have not placed a bet, or the dealer ay have already paid them out.'.format(user=dbUser.real_name))
	else:
		payAmount = float(currentBets[userMentionString] * payoutRatio) # Calculate pay-out amount (current bet * pay-out ratio).
		currentWalletAmount = dbUser.wallet                             # Cache the wallet balance pre-winnings.
		dbUser.update(wallet=currentWalletAmount+float(payAmount))      # Add the money to the user's wallet in the database.

		# Add the win/loss to the user's record in the database.
		if winState == 'win':
			dbUser.update(total_wins=dbUser.total_wins+1)
			dbUser.update(total_winnings=dbUser.total_winnings+(payAmount-currentBets[userMentionString]))
		elif winState == 'loss':
			dbUser.update(total_losses=dbUser.total_losses+1)
			dbUser.update(total_winnings=dbUser.total_winnings-(currentBets[userMentionString]))

		# Remove the user's bet from the in-memory bets table.
		del currentBets[userMentionString]

		return {
			'userWhoGotPaid' : dbUser,
			'payOutTotal'    : payAmount
		}

# -------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------- #
# Define the commands and bot's reactions.

@client.event
async def on_ready():
	print('Logged in as {0.user}'.format(client))
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Death Grips — 'Blackjack'"))

# Checks the user's wallet balance. Creates a wallet if they don't have one already.
@client.command()
async def balance(ctx):
	'''Shows your current wallet balance. Creates a wallet for you if you do not have one.'''
	if userInDatabase(ctx.author.id) == False: # If user not found found in database, create a wallet for them.
		await ctx.send(embed=dialogBox('gear', 'You don\'t have a wallet yet!', 'Creating one with a balance of **{amt}**...'.format(amt=asMoney(defaultWalletAmount))))
		User.create(
			dc_uniqueid  = ctx.author.id,
			dc_username  = ctx.author.name,
			real_name    = ctx.author.display_name,
		)
	dbUser = userInDatabase(ctx.author.id)
	await ctx.send(embed=dialogBox('moneybag', '{name}\'s current wallet balance is {balance}'.format(name=dbUser.real_name, balance=asMoney(dbUser.wallet))))
	if deleteUserMessages == True:
		await ctx.message.delete()

# Open bets. Dealer only.
@client.command()
async def openbets(ctx):
	'''DEALER ONLY. Opens the table for betting, allows users to place bets with $bet <amount>'''
	global betsOpen
	# Only execute if the message author is a dealer.
	if isDealer(ctx.author):
		# Delete all messages in chat
		messages = []
		async for message in ctx.channel.history(limit=int(100)):
			messages.append(message)
		await message.channel.delete_messages(messages)

		# If there are bets existing...
		if bool(currentBets) == True:
			await ctx.send(embed=dialogBox('warning', 'The dealer is yet to pay out some bets.', 'Check the open bets with `$unpaidbets`.'))
		# If bets are already open...
		elif betsOpen:
			await ctx.send(embed=dialogBox('warning', 'Bets are already open', 'Close them with `$closebets`.'))
			# If bets aren't open and there aren't any existing bets, then open bets.
		else:
			betsOpen = True
			await ctx.send(embed=dialogBox('tick', 'Bets are now open!', 'Place your bets with `$bet <number>` (e.g. `$bet 50`)'))

	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

# Close bets. Dealer only.
@client.command()
async def closebets(ctx):
	'''DEALER ONLY. Closes the table for betting, barring players from placing bets with the $bet command'''
	global betsOpen
	if deleteUserMessages == True:
		await ctx.message.delete()

	# Only execute if the message author is a dealer.
	if isDealer(ctx.author):
		# If bets are closed...
		if not betsOpen:
			await ctx.send(embed=dialogBox('warning', 'Bets aren\'t open yet', 'Open them with `$openbets`.'))
		else:
			# Delete all messages in chat
			# messages = []
			# async for message in message.channel.history(limit=int(100)):
			# 	messages.append(message)
			# await message.channel.delete_messages(messages)
			betsOpen = False
			betString = ''
			if bool(currentBets) == True:
				for userID, betValue in currentBets.items():
					betString+='  — **<@!{user}>** has bet **{amount}**.\n'.format(user=userID, amount=asMoney(betValue))
			else:
				betString = 'No bets have been placed...?'

			await ctx.send(embed=dialogBox('raisedhand', 'Bets are now closed!', betString))
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

# Place a bet if the table is accepting them.
@client.command()
async def bet(ctx, betAmount):
	'''If bets are open, places a bet of the specified amount.'''
	global betsOpen
	if deleteUserMessages == True:
		await ctx.message.delete()

	if betsOpen == True:
		betAmount = float(betAmount.strip('$')) # Sanitise input.
		dbUser = userInDatabase(ctx.author.id)
		if dbUser == False:
			await ctx.send(embed=dialogBox('warning', 'You don\'t have a wallet yet!', 'Type `$balance` to create one.'))
		elif ctx.author.id in currentBets:
			dbUser = userInDatabase(ctx.author.id)
			dbUser.update(wallet=dbUser.wallet+currentBets[ctx.author.id]) # Refund the first bet.
			dbUser.update(wallet=dbUser.wallet-betAmount) # Refund the first bet.
			currentBets[ctx.author.id] = betAmount
			await ctx.send(embed=dialogBox('dollar', '{name} has changed their bet to {amount}!'.format(name=dbUser.real_name, amount=asMoney(betAmount)), 'They now have **{amtLeft}** left in their wallet.'.format(amtLeft=asMoney(dbUser.wallet))))
		elif int(betAmount) > dbUser.wallet:
			await ctx.send(embed=dialogBox('warning', 'You\'re trying to bet more money than you have in your wallet!', 'Type `$balance` to see how much you have.'))
		# elif int(betAmount) % 10 != 0:
		# 	await ctx.send(embed=dialogBox('gear', 'Please only bet in multiples of 10, sorry!', 'Jess is lazy and forgot to account for decimal points in the code. This is going to be fixed in a later update.'))
		else: # If the planets align...
			dbUser = userInDatabase(ctx.author.id)              # Get the user from the database.
			currentBets[ctx.author.id] = betAmount              # Add their bet to the in-memory table of bets.
			currentWalletAmount = dbUser.wallet                 # Get the user's current wallet amount from the database.
			dbUser.update(wallet=currentWalletAmount-betAmount) # Take the bet from the user's wallet.

			# Log statistics
			dbUser.update(total_bets=dbUser.total_bets+1)
			Bets.create(bet_user_id=ctx.author.id, bet_amount=betAmount)

			await ctx.send(embed=dialogBox('dollar', '{name} has bet {amount}!'.format(name=dbUser.real_name, amount=asMoney(betAmount)), 'They now have **{amtLeft}** left in their wallet.'.format(amtLeft=asMoney(dbUser.wallet))))
	else:
		await ctx.send(embed=dialogBox('warning', 'Bets aren\'t open yet', 'Get the dealer to open them with `$openbets`.'))

# Pays the user out a specific ratio of their original bet. Dealer only
@client.command()
async def pay(ctx, userMentionString, payoutRatio):
	'''DEALER ONLY. Pays the @'ed user out. For example, `$pay @Jess 2x` will give Jess back $100 on a bet of $50. Ensure that the username after the @ is an actual mention (i.e. it pings the user).'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : float(payoutRatio.strip('x'))
		}

		if payDetails['ratio'] >= 1:
			userWinState = 'win'
		elif payDetails['ratio'] < 1:
			userWinState = 'loss'

		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],userWinState)
		finaldialog = dialogBox(
			'winner',
			'{user} wins!'.format(user=payoutResponse['userWhoGotPaid'].real_name),
			'The house has paid <@!{userID}> a total of **{amount}**, and their wallet balance is now **{balance}**.'.format(
				userID=payoutResponse['userWhoGotPaid'].dc_uniqueid,
				amount=asMoney(payoutResponse['payOutTotal']),
				balance=asMoney(payoutResponse['userWhoGotPaid'].wallet)
			)
		)
		await ctx.send(embed=finaldialog)
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

# Pays the user out 2.5x. Dealer only
@client.command()
async def blackjack(ctx, userMentionString):
	'''DEALER ONLY. An alias of $pay <user> 2.5x.'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : 2.5
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'win')
		finaldialog = dialogBox(
			'blackjack',
			'{user} got blackjack!'.format(user=payoutResponse['userWhoGotPaid'].real_name),
			'The house has paid <@!{userID}> a total of **{amount}**, and their wallet balance is now **{balance}**.'.format(
				userID=payoutResponse['userWhoGotPaid'].dc_uniqueid,
				amount=asMoney(payoutResponse['payOutTotal']),
				balance=asMoney(payoutResponse['userWhoGotPaid'].wallet)
			)
		)
		await ctx.send(embed=finaldialog)
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

# Pays the user out 0x (take their bet). Dealer only
@client.command()
async def bust(ctx, userMentionString):
	'''DEALER ONLY. Takes a user's bet. An alias of $pay <user> 0x.'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : 0
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'loss')
		finaldialog = dialogBox(
			'loser',
			'{user} loses!'.format(user=payoutResponse['userWhoGotPaid'].real_name),
			'The house has taken <@!{userID}>\'s bet, and their wallet balance is now **{balance}**.'.format(
				userID=payoutResponse['userWhoGotPaid'].dc_uniqueid,
				balance=asMoney(payoutResponse['userWhoGotPaid'].wallet)
			)
		)
		await ctx.send(embed=finaldialog)
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.', 'messageContent'))

# Pays the user out 1x (refund their bet). Dealer only
@client.command()
async def push(ctx, userMentionString):
	'''DEALER ONLY. Refunds a user's bet in the event of a push. An alias of $pay <user> 1x.'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : 1
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'push')
		finaldialog = dialogBox(
			'push',
			'{user} pushes!'.format(user=payoutResponse['userWhoGotPaid'].real_name),
			'The house has refunded <@!{userID}>\'s bet of **{amount}**, and their wallet balance is now back at **{balance}**.'.format(
				userID=payoutResponse['userWhoGotPaid'].dc_uniqueid,
				amount=asMoney(payoutResponse['payOutTotal']),
				balance=asMoney(payoutResponse['userWhoGotPaid'].wallet)
			)
		)
		await ctx.send(embed=finaldialog)
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

# View open/standing bets
@client.command(aliases=['currentbets', 'standingbets'])
async def unpaidbets(ctx):
	'''Displays all bets that are yet to be paid out'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	if bool(currentBets) == True: # If bets exist in the bets table...
		embedTitle = "The following bets have been made:"
		standingBets = ''
		for userID, betValue in currentBets.items():
			standingBets +='  — **<@!{user}>\'s** bet of **{amount}**.\n'.format(user=userID, amount=asMoney(betValue))
		await ctx.send(embed=dialogBox('waiting', embedTitle, standingBets))
	else:
		await ctx.send(embed=dialogBox('tick', 'No currently standing bets.'))

# If a bet exists, double it.
@client.command(aliases=['split', 'double'])
async def doubledown(ctx):
	'''Doubles your bet. Can be done at any time, even if bets are closed.'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	dbUser = userInDatabase(ctx.author.id)
	currentWalletAmount = dbUser.wallet
	#await message.delete()
	if ctx.author.id not in currentBets:
		await ctx.send(embed=dialogBox('warning', 'You haven\'t placed a bet.'))
	elif currentBets[ctx.author.id] > dbUser.wallet:
		await ctx.send(embed=dialogBox('warning', 'You\'re trying to double or split your bet, but you don\'t have enough in your wallet to do so.', 'Type `$balance` to see how much you have.'))
	else:
		dbUser.update(wallet=currentWalletAmount-currentBets[ctx.author.id])
		currentBets[user_id] = currentBets[user_id] * 2
		await message.channel.send(':dollar: **<@!{name}> has doubled their bet from ${originalAmount} to ${doubledAmount}!** They now have ${amtLeft} left in their wallet.'.format(name=user_id, originalAmount=currentBets[user_id]/2, doubledAmount=currentBets[user_id], amtLeft=wallets[user_id]))
		await ctx.send(embed=dialogBox(
			'dollar', '<@!{name}> has doubled their bet from ${originalAmount} to ${doubledAmount}!'.format(
				name=ctx.author.id,
				originalAmount=currentBets[ctx.author.id]/2,
				doubledAmount=currentBets[ctx.author.id]
			),
			'They now have ${amtLeft} left in their wallet.'.format(
				amtLeft=wallets[ctx.author.id]
			)
		))

# Show the strategy chart
@client.command(aliases=['strat', 'strategy', 'chart', 'basicstrategy'])
async def strats(ctx):
	'''Shows the basic Blackjack strategy chart'''
	if deleteUserMessages == True:
		await ctx.message.delete()

	await ctx.channel.send('https://cdn.discordapp.com/attachments/734766427583676479/734767587157868664/BJA_Basic_Strategy.png')

# Allows the dealer to buy-in a user.
@client.command()
async def buyin(ctx, userMentionString):
	'''DEALER ONLY. Adds $100 to a user's wallet.'''
	if deleteUserMessages == True:
		await ctx.message.delete()
	if isDealer(ctx.author):
		dbUser = userInDatabase(userMentionString[3:-1])
		dbUser.update(wallet=dbUser.wallet+float(100))
		dbUser.update(total_buyins=dbUser.total_buyins+1)
		await ctx.send(embed=dialogBox(
			'handshake', '{} has bought in!'.format(dbUser.real_name),
			'The dealer has topped up {name}\'s wallet with an extra **$100**, bringing their funds up to **{amt}**.'.format(name=dbUser.real_name, amt=asMoney(dbUser.wallet))
		))
	else:
		await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command', 'messageContent'))

@client.event
async def on_command_error(ctx, error):
	await ctx.send(embed=dialogBox(
		'error', 'An error has occurred'.format(dbUser.real_name),
		'`{}`'.format(error)
	)
	print('test')

@client.command()
async def getemoji(ctx):
	emojilist = []
	for emoji in ctx.guild.emojis:
		emojilist.append('{name} ({id})'.format(name=emoji.id, id=emoji.name))
	await ctx.send(embed=debugMessage(json.dumps(emojilist,indent=4)))

# -------------------------------------------------------------------------------------------- #

client.run(blacktrack_token.botToken())
# 83333350588157952
