import discord
import json
import pprint
import blacktrack_token

client = discord.Client()
TOKEN = blacktrack_token.botToken()

pp = pprint.PrettyPrinter(indent=4)
wallets = {}
currentBets = {} # A dict containing user IDs and their corresponding bet.
betsOpen = False # Whether or not the table is accepting new bets.
channeltoWatch = 735381840835379259

helpString = ''':black_joker: **BlackTrack Bot v0.2.0**
Written by Jess Merriman (github.com/ChainsawPolice)

**Player commands:**
`$balance`: Shows your current wallet balance. Creates a wallet for you if you do not have one.
`$bet <amount>`: If bets are open, places a bet of the specified amount. Make sure to not include a dollar sign; just type the number itself.
`$unpaidbets`: Displays all bets that are yet to be paid out.
`$doubledown`: Doubles your bet. Can be done at any time, even if bets are closed.
`$strats`: Shows the basic Blackjack strategy chart.
`$help`: Does what it says on the tin.

**Dealer-only commands:**
`$openbets`: Opens the table for betting, allows users to place bets with `$bet <amount>`.
`$closebets` Closes the table for betting.
`$pay <user> <ratio>`: Pays the @'ed user out. For example, `$pay @Jess 2x` will give Jess back $100 on a bet of $50. Ensure that the username after the @ is an actual mention (i.e. it pings the user).'
`$bust <user>`: Takes the user's bet. As with `$pay`, ensure that the username after the @ is an actual mention (i.e. it pings the user).
`$push <user>`: Refunds the user's bet in the event of a push. As with `$pay`, ensure that the username after the @ is an actual mention (i.e. it pings the user).'''

# -------------------------------------------------------------------------------------------- #

def isDealer(userObject):
	listOfRoleIDs = []
	for role in userObject.roles:
		listOfRoleIDs.append(role.id)
	if 735351625899573341 in listOfRoleIDs:
		return True
	else:
		return False

# -------------------------------------------------------------------------------------------- #

@client.event
async def on_ready():
	print('Logged in as {0.user}'.format(client))
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Death Grips — 'Blackjack'"))

@client.event
async def on_message(message):
	user_id = str(message.author.id) #Makes things easier down the track.
	global betsOpen
	global currentBets

	# Ignore own messages, lmao.
	if message.author == client.user:
		return

	# Debug.
	if message.content.startswith('$debug bets'):
		await message.channel.send('`currentBets = {}`'.format(json.dumps(currentBets, indent=4)))
		await message.channel.send('`{}`'.format(bool(currentBets)))
	if message.content.startswith('$debug wallets'):
		await message.channel.send('`wallets = {}`'.format(json.dumps(wallets, indent=4)))
	if message.content.startswith('$hello'):
		await message.channel.send('Hello there, '+str(message.author)+'!')
		await message.channel.send('Your user ID is `'+str(message.author.id)+'`.')
		await message.channel.send('Your message was `'+str(message.content)+'`.')
	if message.content.startswith('$debug roles'):
		listOfRoles = []
		for role in message.author.roles:
			listOfRoles.append({'RoleName':role.name, 'ID':role.id})
		await message.channel.send('`{}`'.format(json.dumps(listOfRoles,indent=4)))
	if message.content.startswith('$debug isdealer'):
		if isDealer(message.author):
			await message.channel.send('`{} is a dealer and thus has access to dealer-only commands.`'.format(message.author))
		else:
			await message.channel.send('`{} is not a dealer.`'.format(message.author))
	if message.content.startswith('$debug clear'):
		channel = message.channel
		messages = []
		async for message in channel.history(limit=int(100)):
			messages.append(message)
		await channel.delete_messages(messages)

	# Check balance. Creates a wallet if the user doesn't have one yet.
	if message.content.startswith('$balance'):
		await message.delete()
		if user_id not in wallets:
			await message.channel.send(':hourglass: You don\'t have a wallet yet! Creating one with a balance of $200...')
			wallets[user_id] = 200
		await message.channel.send(':moneybag: <@!{name}>\'s current wallet balance is **${balance}**'.format(name=user_id, balance=wallets[user_id]))
		print(json.dumps(wallets, indent=4))

	# Open bets. Dealer only.
	if message.content.startswith('$openbets'):
		# Only execute if the message author is a dealer.
		if isDealer(message.author):
			# Delete all messages in chat
			messages = []
			async for message in message.channel.history(limit=int(100)):
				messages.append(message)
			await message.channel.delete_messages(messages)

			# If there are bets existing...
			if bool(currentBets) == True:
				await message.channel.send(':no_entry: **The dealer is yet to pay out some bets.** Check the open bets with `$unpaidbets`.')
			# If bets are already open...
			elif betsOpen:
				await message.channel.send(':hourglass: Bets are already open. Close them with `$closebets`.')
			# If bets aren't open and there aren't any existing bets, then open bets.
			else:
				betsOpen = True
				await message.channel.send(':white_check_mark: **Bets are now open!** Place your bets with `$bet <number>` (e.g. `$bet 50`)')
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# Close bets. Dealer only.
	if message.content.startswith('$closebets'):
		# Only execute if the message author is a dealer.
		if isDealer(message.author):
			await message.delete()
			# If bets are closed...
			if not betsOpen:
				await message.channel.send(':hourglass: Bets aren\'t open yet. Open them with `$openbets`.')
			else:
				# Delete all messages in chat
				# messages = []
				# async for message in message.channel.history(limit=int(100)):
				# 	messages.append(message)
				# await message.channel.delete_messages(messages)
				betsOpen = False
				await message.channel.send(':no_entry: **Bets are now closed!**')
				if bool(currentBets) == True:
					messageToSend = ":moneybag: The following bets have been made:\n"
					for userID, betValue in currentBets.items():
						messageToSend+='  — **<@!{user}>** has bet **${amount}** _(${remainingBalance} remaining in wallet)_.\n'.format(user=userID, amount=betValue, remainingBalance=wallets[userID])
					await message.channel.send(messageToSend)
				else:
					await message.channel.send(':dink: No bets have been placed...?')
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# Place bet.
	if message.content.startswith('$bet'):
		await message.delete()
		if betsOpen == True:
			betAmount = int(message.content.split()[1].strip('$'))

			if user_id not in wallets:
				await message.channel.send(':no_entry: You don\'t have a wallet yet! Type `$balance` to create one.')
			elif user_id in currentBets:
				await message.channel.send(':no_entry: You\'ve already placed a bet!'.format(name=user_id, amount=betAmount))
			elif int(betAmount) > wallets[user_id]:
				await message.channel.send(':no_entry: You\'re trying to bet more money than you have in your wallet. Type `$balance` to see how much you have.')
			elif int(betAmount) % 10 != 0:
				await message.channel.send(':no_entry: Please only bet in multiples of 10, sorry _(Jess is lazy and forgot to account for decimal points in the code :dink: )_')
			else:
				currentBets[user_id] = betAmount
				wallets[user_id] = wallets[user_id]-betAmount
				await message.channel.send(':dollar: **<@!{name}> has bet ${amount}!** They now have **${amtLeft}** left in their wallet.'.format(name=user_id, amount=betAmount, amtLeft=wallets[user_id]))
				print(json.dumps(currentBets, indent=4))
		else:
			await message.channel.send(':no_entry: Bets aren\'t open yet. The dealer must open them with `$openbets`.')

	# Pay user n times. Dealer only.
	if message.content.startswith('$pay'):
		await message.delete()
		if isDealer(message.author):
			payCommand = message.content.split()
			payDetails = {
				'user' 	: payCommand[1][3:-1],
				'ratio' : float(payCommand[2].strip('x'))
			}
			if payDetails['user'] not in currentBets:
				await message.channel.send(':no_entry: No bets currently standing for <@!{user}>.'.format(user=payDetails['user']))
			else:
				payAmount = currentBets[payDetails['user']] * payDetails['ratio']
				del currentBets[payDetails['user']]
				wallets[payDetails['user']] = int(wallets[payDetails['user']]) + int(payAmount)
				await message.channel.send(':partying_face: **<@!{user}> wins!** The house has paid them ${amount}, and their balance is now ${balance}.'.format(user=payDetails['user'],amount=payAmount, balance=wallets[payDetails['user']]))
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# User got blackjack, pay them 2.5x. Dealer only.
	if message.content.startswith('$blackjack'):
		await message.delete()
		if isDealer(message.author):
			payCommand = message.content.split()
			payDetails = {
				'user' 	: payCommand[1][3:-1],
				'ratio' : 2.5
			}
			if payDetails['user'] not in currentBets:
				await message.channel.send(':no_entry: No bets currently standing for <@!{user}>.'.format(user=payDetails['user']))
			else:
				payAmount = currentBets[payDetails['user']] * payDetails['ratio']
				del currentBets[payDetails['user']]
				wallets[payDetails['user']] = int(wallets[payDetails['user']]) + int(payAmount)
				await message.channel.send(':gem: **<@!{user}> got blackjack!** The house has paid them ${amount}, and their balance is now ${balance}.'.format(user=payDetails['user'],amount=payAmount, balance=wallets[payDetails['user']]))
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# User busts. Dealer only.
	if message.content.startswith('$bust'):
		await message.delete()
		if isDealer(message.author):
			payCommand = message.content.split()
			payDetails = {
				'user' 	: payCommand[1][3:-1],
				'ratio' : 0
			}
			if payDetails['user'] not in currentBets:
				await message.channel.send(':no_entry: No bets currently standing for <@!{user}>.'.format(user=payDetails['user']))
			else:
				userBet = currentBets[payDetails['user']]
				newBalance = wallets[payDetails['user']]
				del currentBets[payDetails['user']]
				await message.channel.send(':pensive: **<@!{user}> has lost!** The house takes their bet of **${amount}**! <@!{user}>\'s balance is now ${balance}'.format(user=payDetails['user'],amount=userBet, balance=newBalance))
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# User pushes. Dealer only.
	if message.content.startswith('$push'):
		await message.delete()
		if isDealer(message.author):
			payCommand = message.content.split()
			payDetails = {
				'user' 	: payCommand[1][3:-1],
				'ratio' : 0
			}
			if payDetails['user'] not in currentBets:
				await message.channel.send(':no_entry: No bets currently standing for <@!{user}>.'.format(user=payDetails['user']))
			else:
				userBet = currentBets[payDetails['user']]
				wallets[payDetails['user']] = wallets[payDetails['user']] + currentBets[payDetails['user']]
				del currentBets[payDetails['user']]
				await message.channel.send(':right_facing_fist: **<@!{user}> pushes** and takes back their bet of **${amount}**! <@!{user}>\'s balance is now ${balance}'.format(user=payDetails['user'],amount=userBet, balance=wallets[payDetails['user']]))
		else:
			await message.channel.send(':no_entry: **Only the dealer has access to this command.**')

	# View open bets.
	if message.content.startswith('$unpaidbets') or message.content.startswith('$currentbets'):
		await message.delete()
		if bool(currentBets) == True:
			if message.content.startswith('$unpaidbets'):
				messageToSend = ":hourglass: **The house is still yet to pay out the following bets:**\n"
			elif message.content.startswith('$currentbets'):
				messageToSend = ":hourglass: The following bets have been made:\n"
			for userID, betValue in currentBets.items():
				messageToSend+='  — **<@!{user}>\'s** bet of **${amount}**.\n'.format(user=userID, amount=betValue)
			await message.channel.send(messageToSend)
		else:
			await message.channel.send(':white_check_mark: All bets have been paid!')

	# If a bet exists, double it.
	if message.content.startswith('$doubledown') or message.content.startswith('$split'):
		await message.delete()
		if user_id not in wallets:
			await message.channel.send(':no_entry: You don\'t have a wallet yet! Type `$balance` to create one.')
		elif user_id not in currentBets:
			await message.channel.send(':no_entry: You haven\'t placed a bet yet.')
		elif currentBets[user_id] > wallets[user_id]:
			await message.channel.send(':no_entry: You\'re trying to double or split your bet, but you don\'t have enough in your wallet to do so. Type `$balance` to see how much you have.')
		else:
			wallets[user_id] = wallets[user_id]-currentBets[user_id]
			currentBets[user_id] = currentBets[user_id] * 2
			await message.channel.send(':dollar: **<@!{name}> has doubled their bet from ${originalAmount} to ${doubledAmount}!** They now have ${amtLeft} left in their wallet.'.format(name=user_id, originalAmount=currentBets[user_id]/2, doubledAmount=currentBets[user_id], amtLeft=wallets[user_id]))

	# Show the strategy chart
	if message.content.startswith('$strats'):
		await message.delete()
		await message.channel.send('https://cdn.discordapp.com/attachments/734766427583676479/734767587157868664/BJA_Basic_Strategy.png')

	if message.content.startswith('$help'):
		await message.delete()
		await message.channel.send(helpString)

client.run(TOKEN)
