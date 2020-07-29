import discord
from discord.ext import commands
import json

from btmodules.blacktrack_token import botToken
from btmodules.common_utils import asMoney, isDealer, getAvatarURL, convertMentionToID
from btmodules.ui_tools import dialogBox, debugMessage
from btmodules.db_utils import User, Bets, userInDatabase, initDatabase, largestBet
import btmodules.global_constants as global_constants

# Instantiate the bot's Discord session.
client = commands.Bot(command_prefix='$')

# Global variables
currentBets = {}
betsOpen = False

# -------------------------------------------------------------------------------------------- #
#Useful functions

# Run a query to see if a user exists in the database already. Returns the query object if found, False if not.
# TODO: Clean up this god-forgotten mess of sellotaped-together code.

# Pay out a user
def payUserOut(ctx,userMention, payoutRatio,winState):
	'''Takes the user's ID, pay-out ratio, and win-state. Pays out the user, tracks it in the database, then returns the user's name and pay-out amount.'''
	userID = convertMentionToID(userMention) # Chop of the first three chars and the last one.
	dbUser = userInDatabase(userID)
	print(payoutRatio)

	if userID not in currentBets:
		return False
	else:
		payAmount = float(currentBets[userID] * float(str(payoutRatio).strip('x'))) # Calculate pay-out amount (current bet * pay-out ratio).
		currentWalletAmount = dbUser.wallet                             # Cache the wallet balance pre-winnings.
		dbUser.update(wallet=currentWalletAmount+float(payAmount))      # Add the money to the user's wallet in the database.

		# Add the win/loss to the user's record in the database.
		if winState == 'win' or winState == 'blackjack':
			dbUser.update(total_wins=dbUser.total_wins+1)
			dbUser.update(total_winnings=dbUser.total_winnings+(payAmount-currentBets[userID]))
		elif winState == 'loss':
			dbUser.update(total_losses=dbUser.total_losses+1)
			dbUser.update(total_winnings=dbUser.total_winnings-(currentBets[userID]))

		# Remove the user's bet from the in-memory bets table.
		del currentBets[userID]
		return payAmount

# -------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------- #
# Define the commands and bot's reactions.

@client.event
async def on_ready():
	print('Logged in as {0.user}.'.format(client))
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Death Grips — 'Blackjack'"))

# Checks the user's wallet balance. Creates a wallet if they don't have one already.
@client.command()
async def balance(ctx):
	'''Shows your current wallet balance. Creates a wallet for you if you do not have one.'''
	if ctx.message.channel.id in global_constants.validChannels:
		if userInDatabase(ctx.author.id) == False: # If user not found found in database, create a wallet for them.
			await ctx.send(embed=dialogBox('gear', 'You don\'t have a wallet yet!', 'Creating one with a balance of **{amt}**...'.format(amt=asMoney(global_constants.defaultWalletAmount))))
			User.create(
				dc_uniqueid  = ctx.author.id,
				dc_username  = ctx.author.name,
				real_name    = ctx.author.display_name,
			)
		dbUser = userInDatabase(ctx.author.id)
		await ctx.send(embed=dialogBox('moneybag', '{name}\'s current wallet balance is {balance}'.format(name=dbUser.real_name, balance=asMoney(dbUser.wallet))))
		if global_constants.deleteUserMessages == True:
			await ctx.message.delete()

# Open bets. Dealer only.
@client.command()
async def openbets(ctx):
	'''DEALER ONLY. Opens the table for betting, allows users to place bets with $bet <amount>'''
	global betsOpen
	if ctx.message.channel.id in global_constants.validChannels:
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
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# Close bets. Dealer only.
@client.command()
async def closebets(ctx):
	'''DEALER ONLY. Closes the table for betting, barring players from placing bets with the $bet command'''
	global betsOpen
	if ctx.message.channel.id in global_constants.validChannels:
		if global_constants.deleteDealerMessages == True:
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
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# Place a bet if the table is accepting them.
@client.command()
async def bet(ctx, betAmount):
	'''If bets are open, places a bet of the specified amount.'''
	global betsOpen
	if ctx.message.channel.id in global_constants.validChannels:
		if global_constants.deleteUserMessages == True:
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
	if ctx.message.channel.id in global_constants.validChannels:
		if isDealer(ctx.author):
			if global_constants.deleteDealerMessages == True:
				await ctx.message.delete()
			dbUser = userInDatabase(int(convertMentionToID(userMentionString)))
			if int(convertMentionToID(userMentionString)) not in currentBets:
				await ctx.send(dialogBox('warning', 'No bets currently standing for this user.', 'They may have not placed a bet, or the dealer may have already paid them out.'))
			else:
				payoutResponse = payUserOut(ctx,userMentionString,payoutRatio,'win')
				finaldialog = dialogBox(
					'winner',
					'{user} wins!'.format(user=dbUser.real_name),
					'The house has paid <@!{userID}> a total of **{amount}**, and their wallet balance is now **{balance}**.'.format(
						userID=dbUser.dc_uniqueid,
						amount=asMoney(payoutResponse),
						balance=asMoney(dbUser.wallet)
					)
				)
				finaldialog.set_thumbnail(url=getAvatarURL(ctx,dbUser.dc_uniqueid))
				await ctx.send(embed=finaldialog)
		else:
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# Pays the user out 2.5x. Dealer only
@client.command()
async def blackjack(ctx, userMentionString):
	'''DEALER ONLY. An alias of $pay <user> 2.5x.'''
	payoutRatio = 2.5
	if ctx.message.channel.id in global_constants.validChannels:
		if isDealer(ctx.author):
			if global_constants.deleteDealerMessages == True:
				await ctx.message.delete()
			dbUser = userInDatabase(int(convertMentionToID(userMentionString)))
			if int(convertMentionToID(userMentionString)) not in currentBets:
				await ctx.send(dialogBox('warning', 'No bets currently standing for this user.', 'They may have not placed a bet, or the dealer may have already paid them out.'))
			else:
				payoutResponse = payUserOut(ctx,userMentionString,payoutRatio,'win')
				finaldialog = dialogBox(
					'blackjack',
					'{user} got blackjack!'.format(user=dbUser.real_name),
					'The house has paid <@!{userID}> a total of **{amount}**, and their wallet balance is now **{balance}**.'.format(
						userID=dbUser.dc_uniqueid,
						amount=asMoney(payoutResponse),
						balance=asMoney(dbUser.wallet)
					)
				)
				finaldialog.set_thumbnail(url=getAvatarURL(ctx,dbUser.dc_uniqueid))
				await ctx.send(embed=finaldialog)
		else:
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# Pays the user out 0x (take their bet). Dealer only
@client.command()
async def bust(ctx, userMentionString):
	'''DEALER ONLY. Takes a user's bet. An alias of $pay <user> 0x.'''
	if ctx.message.channel.id in global_constants.validChannels:
		if isDealer(ctx.author):
			if global_constants.deleteDealerMessages == True:
				await ctx.message.delete()
			dbUser = userInDatabase(int(convertMentionToID(userMentionString)))
			if int(convertMentionToID(userMentionString)) not in currentBets:
				await ctx.send(dialogBox('warning', 'No bets currently standing for this user.', 'They may have not placed a bet, or the dealer may have already paid them out.'))
			else:
				payoutResponse = payUserOut(ctx,userMentionString,0,'win')
				finaldialog = dialogBox(
					'loser',
					'{user} loses!'.format(user=dbUser.real_name),
					'The house has taken <@!{userID}>\'s bet, and their wallet balance is now **{balance}**.'.format(
						userID=dbUser.dc_uniqueid,
						amount=asMoney(payoutResponse),
						balance=asMoney(dbUser.wallet)
					)
				)
				finaldialog.set_thumbnail(url=getAvatarURL(ctx,dbUser.dc_uniqueid))
				await ctx.send(embed=finaldialog)
		else:
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# Pays the user out 1x (refund their bet). Dealer only
@client.command()
async def push(ctx, userMentionString):
	'''DEALER ONLY. Refunds a user's bet in the event of a push. An alias of $pay <user> 1x.'''
	if ctx.message.channel.id in global_constants.validChannels:
		if isDealer(ctx.author):
			if global_constants.deleteDealerMessages == True:
				await ctx.message.delete()
			dbUser = userInDatabase(int(convertMentionToID(userMentionString)))
			if int(convertMentionToID(userMentionString)) not in currentBets:
				await ctx.send(dialogBox('warning', 'No bets currently standing for this user.', 'They may have not placed a bet, or the dealer may have already paid them out.'))
			else:
				payoutResponse = payUserOut(ctx,userMentionString,1,'win')
				finaldialog = dialogBox(
					'push',
					'{user} pushes!'.format(user=dbUser.real_name),
					'The house has refunded <@!{userID}>\'s bet of **{amount}**, and their wallet balance is now back at **{balance}**.'.format(
						userID=dbUser.dc_uniqueid,
						amount=asMoney(payoutResponse),
						balance=asMoney(dbUser.wallet)
					)
				)
				finaldialog.set_thumbnail(url=getAvatarURL(ctx,dbUser.dc_uniqueid))
				await ctx.send(embed=finaldialog)
		else:
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

# View open/standing bets
@client.command(aliases=['currentbets', 'standingbets'])
async def unpaidbets(ctx):
	'''Displays all bets that are yet to be paid out'''
	if ctx.message.channel.id in global_constants.validChannels:
		if global_constants.deleteUserMessages == True:
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
	if ctx.message.channel.id in global_constants.validChannels:
		if global_constants.deleteUserMessages == True:
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
			currentBets[ctx.author.id] = currentBets[ctx.author.id] * 2
			dbUser = userInDatabase(ctx.author.id)
			await ctx.send(':dollar: **<@!{name}> has doubled their bet from ${originalAmount} to ${doubledAmount}!** They now have ${amtLeft} left in their wallet.'.format(name=ctx.author.id, originalAmount=currentBets[ctx.author.id]/2, doubledAmount=currentBets[ctx.author.id], amtLeft=dbUser.wallet]))
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
	if ctx.message.channel.id in global_constants.validChannels:
		if global_constants.deleteUserMessages == True:
			await ctx.message.delete()

		await ctx.channel.send('https://cdn.discordapp.com/attachments/734766427583676479/734767587157868664/BJA_Basic_Strategy.png')

# Allows the dealer to buy-in a user. Dealer only.
@client.command()
async def buyin(ctx, userMentionString):
	'''DEALER ONLY. Adds $100 to a user's wallet.'''
	if ctx.message.channel.id in global_constants.validChannels:
		if isDealer(ctx.author):
			if global_constants.deleteDealerMessages == True:
				await ctx.message.delete()
			dbUser = userInDatabase(convertMentionToID(userMentionString))
			dbUser.update(wallet=dbUser.wallet+float(100))
			dbUser.update(total_buyins=dbUser.total_buyins+1)
			await ctx.send(embed=dialogBox(
				'handshake', '{} has bought in!'.format(dbUser.real_name),
				'The dealer has topped up {name}\'s wallet with an extra **$100**, bringing their funds up to **{amt}**.'.format(name=dbUser.real_name, amt=asMoney(dbUser.wallet))
			))
		else:
			await ctx.send(embed=dialogBox('error', 'Only the dealer has access to this command.'))

@client.command()
async def insurance(ctx):
	if ctx.message.channel.id in global_constants.validChannels:
		await ctx.send(embed=debugMessage('Still working on this one...'))

@client.command()
async def stats(ctx,userMention=''):
	'''Pull up the lifetime stats for yourself or another user.'''
	if ctx.message.channel.id in global_constants.validChannels:
		# If a user was mentioned, pull the database record for them.
		# If no mention, default to using the author's message ID as passed through via context.
		if userMention:
			dbUser = userInDatabase(convertMentionToID(userMention))
		else:
			dbUser = userInDatabase(ctx.author.id)

		# Check if user exists in database. If so, collect stats and display them.
		if dbUser == False:
			None
		else:
			largestBetInfo = largestBet(dbUser.dc_uniqueid)
			finaldialog = dialogBox('die','Lifetime statistics for {user}'.format(user=dbUser.real_name))
			finaldialog.set_thumbnail(url=getAvatarURL(ctx,dbUser.dc_uniqueid))
			finaldialog.add_field(name='Total funds:' , value=asMoney(dbUser.wallet), inline=True)
			finaldialog.add_field(name='Hands played:', value=dbUser.total_bets     , inline=True)
			finaldialog.add_field(name='Wins:'        , value=dbUser.total_wins     , inline=True)
			finaldialog.add_field(name='Losses:'      , value=dbUser.total_losses   , inline=True)
			finaldialog.add_field(name='Buy-ins:'     , value=dbUser.total_buyins   , inline=True)
			finaldialog.add_field(name='Largest bet:' , value='{amount} at {time}'.format(amount=asMoney(largestBetInfo['betAmount']), time=largestBetInfo['betTime'], winorlose=largestBetInfo['wasAWin']), inline=True)
			# finaldialog.set_footer(text='Wins include blackjacks and any payouts of at least 1.1x and above. The largest bet will not show whether the bet was a win or a loss if the bet was made before PLACEHOLDER.')

			await ctx.send(embed=finaldialog)

@client.command()
async def channelid(ctx,userMention=''):
	await ctx.send(ctx.message.channel.id)

# -------------------------------------------------------------------------------------------- #
if __name__ == '__main__':
	print('Logging in...')
	client.run(botToken)
