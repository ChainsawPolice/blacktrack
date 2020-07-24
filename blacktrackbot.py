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
uiEmoji = {
	'tick'       : [':white_check_mark:', discord.Colour.green()],
	'dollar'     : [':dollar:', discord.Colour.green()],

	'gear'       : [':gear:', discord.Colour.lighter_grey()],

	'warning'    : [':warning:', discord.Colour.gold()],
	'moneybag'   : [':moneybag:', discord.Colour.gold()],
	'waiting'    : [':hourglass:', discord.Colour.gold()],

	'winner'	 : [':partying_face:', discord.Colour.blue()],
	'loser'	     : [':pensive:', discord.Colour.blue()],
	'push'	     : [':right_facing_fist:', discord.Colour.blue()],
	'blackjack'	 : [':brown_square:', discord.Colour.blue()],

	'error'      : [':no_entry:', discord.Colour.red()],
	'raisedhand' : [':raised_hand:', discord.Colour.red()],
}
defaultWalletAmount = 200

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
	return "${:,.2f}".format(value)

# Pay out a user
def payUserOut(ctx,userMentionString, payoutRatio,winState):
	dbUser = userInDatabase(ctx.author.id)

	if userMentionString not in currentBets:
		return dialogBox('warning', 'No bets currently standing for {user}.', 'They may have not placed a bet, or the dealer ay have already paid them out.'.format(user=dbUser.real_name))
	else:
		payAmount = float(currentBets[userMentionString] * payoutRatio) # Calculate pay-out amount (current bet * pay-out ratio).
		del currentBets[userMentionString]                                      # Remove the user's bet from the in-memory bets table.
		currentWalletAmount = dbUser.wallet                                      # Cache the wallet balance pre-winnings.
		dbUser.update(wallet=currentWalletAmount+float(payAmount))               # Add the money to the user's wallet in the database.
		return {
			'userWhoGotPaid' : dbUser,
			'payOutTotal'    : payAmount
		}

# -------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------- #
# Set up database connection
db = ActiveAlchemy('sqlite:///blacktrack.db')
class User(db.Model):
	dc_uniqueid  = db.Column(db.String(100))
	dc_username  = db.Column(db.String(100))
	real_name    = db.Column(db.String(100))
	wallet       = db.Column(db.Integer)
	total_bets   = db.Column(db.Integer)
	total_wins   = db.Column(db.Integer)
	total_losses = db.Column(db.Integer)
	total_buyins = db.Column(db.Integer)

class Bets(db.Model):
	bet_user_id = db.Column(db.String(25))
	bet_amount = db.Column(db.Integer)
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
	# await message.delete()
	if userInDatabase(ctx.author.id) == False: # If user not found found in database, create a wallet for them.
		await ctx.send(embed=dialogBox('gear', 'You don\'t have a wallet yet!', 'Creating one with a balance of **{amt}**...'.format(amt=asMoney(defaultWalletAmount))))
		User.create(
			dc_uniqueid  = ctx.author.id,
			dc_username  = ctx.author.name,
			real_name    = ctx.author.display_name,
			wallet       = defaultWalletAmount,
			total_bets   = 0,
			total_wins   = 0,
			total_losses = 0,
			total_buyins = 0
		)
	dbUser = userInDatabase(ctx.author.id)
	await ctx.send(embed=dialogBox('moneybag', '{name}\'s current wallet balance is {balance}'.format(name=dbUser.real_name, balance=asMoney(dbUser.wallet))))

# Open bets. Dealer only.
@client.command()
async def openbets(ctx):
	'''DEALER ONLY. Opens the table for betting, allows users to place bets with $bet <amount>'''
	global betsOpen
	# Only execute if the message author is a dealer.
	if isDealer(ctx.author):
		# # Delete all messages in chat
		# messages = []
		# async for message in ctx.channel.history(limit=int(100)):
		# 	messages.append(message)
		# await message.channel.delete_messages(messages)

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
	# Only execute if the message author is a dealer.
	if isDealer(ctx.author):
		# await message.delete()
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
	# await message.delete()
	if betsOpen == True:
		betAmount = float(betAmount.strip('$')) # Sanitise input.

		if userInDatabase(ctx.author.id) == False:
			await ctx.send(embed=dialogBox('warning', 'You don\'t have a wallet yet!', 'Type `$balance` to create one.'))
		elif ctx.author.id in currentBets:
			await ctx.send(embed=dialogBox('warning', 'You\'ve already placed a bet!', 'message'))
		elif int(betAmount) > userInDatabase(ctx.author.id).wallet:
			await ctx.send(embed=dialogBox('warning', 'You\'re trying to bet more money than you have in your wallet!', 'Type `$balance` to see how much you have.'))
		# elif int(betAmount) % 10 != 0:
		# 	await ctx.send(embed=dialogBox('gear', 'Please only bet in multiples of 10, sorry!', 'Jess is lazy and forgot to account for decimal points in the code. This is going to be fixed in a later update.'))
		else: # If the planets align...
			dbUser = userInDatabase(ctx.author.id)              # Get the user from the database.
			currentBets[ctx.author.id] = betAmount              # Add their bet to the in-memory table of bets.
			currentWalletAmount = dbUser.wallet                 # Get the user's current wallet amount from the database.
			dbUser.update(wallet=currentWalletAmount-betAmount) # Take the bet from the user's wallet.

			await ctx.send(embed=dialogBox('dollar', '{name} has bet {amount}!'.format(name=dbUser.real_name, amount=asMoney(betAmount)), 'They now have **{amtLeft}** left in their wallet.'.format(amtLeft=asMoney(dbUser.wallet))))
	else:
		await ctx.send(embed=dialogBox('warning', 'Bets aren\'t open yet', 'Get the dealer to open them with `$openbets`.'))

# Pays the user out a specific ratio of their original bet. Dealer only
@client.command()
async def pay(ctx, userMentionString, payoutRatio):
	'''DEALER ONLY. Pays the @'ed user out. For example, `$pay @Jess 2x` will give Jess back $100 on a bet of $50. Ensure that the username after the @ is an actual mention (i.e. it pings the user).'''
	# await message.delete()
	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : float(payoutRatio.strip('x'))
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'win')
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
	# await message.delete()
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
	# await message.delete()
	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : 0
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'win')
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
	# await message.delete()
	if isDealer(ctx.author):
		payDetails = {
			'user' 	: int(userMentionString[3:-1]),
			'ratio' : 1
		}
		payoutResponse = payUserOut(ctx,payDetails['user'],payDetails['ratio'],'win')
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
	if bool(currentBets) == True: # If bets exist in the bets table...
		# await message.delete()
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
	dbUser = userInDatabase(ctx.author.id)
	#await message.delete()
	if user_id not in currentBets:
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
@client.command(aliases=['strat', 'strategy', 'chart', 'basicstrategy'], hidden=True)
async def strats(ctx):
	'''Shows the basic Blackjack strategy chart'''
	await message.channel.send('https://cdn.discordapp.com/attachments/734766427583676479/734767587157868664/BJA_Basic_Strategy.png')
	# await message.delete()

# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG  #
@client.command(hidden=True)
async def debug(ctx):
	'''A command used for debugging randomg things. If this made it to live, yell at Jess for me.'''
	await ctx.send(embed=dialogBox('tick', 'Test message', 'messageContent `test`'))

# -------------------------------------------------------------------------------------------- #

client.run(blacktrack_token.botToken())
