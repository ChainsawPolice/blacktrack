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
	'gear'       : [':gear:', discord.Colour.lighter_grey()],
	'error'      : [':no_entry:', discord.Colour.red()],
	'warning'    : [':warning:', discord.Colour.gold()],
	'raisedhand' : [':raised_hand:', discord.Colour.red()],
	'moneybag'   : [':moneybag:', discord.Colour.gold()],
	'dollar'     : [':dollar:', discord.Colour.green()],
	'winner'	 : [':partying_face:', discord.Colour.blue()],
	'loser'	     : [':pensive:', discord.Colour.blue()],
	'push'	     : [':right_facing_fist:', discord.Colour.blue()],
	'blackjack'	 : [':brown_square:', discord.Colour.blue()],
}
defaultWalletAmount = 200

# -------------------------------------------------------------------------------------------- #
#Useful functions

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

# Create a message.
def dialogBox(messageEmoji, messageTitle, messageContent='', accentColour='inherit'):
	embed = discord.Embed(
		title = '{emoji}  {title}'.format(emoji=uiEmoji[messageEmoji][0], title=messageTitle),
		description = messageContent,
		colour = uiEmoji[messageEmoji][1]
	)
	return embed
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
	await ctx.send(embed=dialogBox('moneybag', '{name}\'s current wallet balance is {balance}'.format(name=dbUser.real_name, balance=asMoney(dbUser.wallet)), 'Happy betting!'))

# Open bets. Dealer only.
@client.command()
async def openbets(ctx):
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

# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG  #
@client.command()
async def debug(ctx):
	await ctx.send(embed=dialogBox('tick', 'Test message', 'messageContent `test`'))

# @client.command(aliases=['initdatabase','startdb'])
# async def initdb(ctx):
# 	await ctx.send('`Initialising database...`')
# 	db.create_all()
# 	await ctx.send('`Done! Check the console for any errors.`')

# -------------------------------------------------------------------------------------------- #

client.run(blacktrack_token.botToken())
