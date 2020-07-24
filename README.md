# BlackTrack
A bet tracker for webcam games of blackjack.
This bot does not play blackjack; it simply tracks bets for the purpose of the cards being dealt via a webcam sharing session.

## Changelog

### v0.2.4
#### Functionality


#### Code
* Cleaned up database model.
* The bot will now log all bets to the database for lifetime statistics tracking. A command to check these stats will be coming shortly.

### v0.2.3
* The previous bug wasn't actually fixed. Fixed and tested to confirm.
* Fixed a bug where `$balance` wouldn't work sometimes due to the message being deleted too soon.

### v0.2.2
* Fixed a bug in which creating a new wallet failed _(wallet value was int, not float)_.

### v0.2.1
* Commands will now be deleted once executed _(back to v0.1.0 functionality)_.
* Fixed the bug/oversight where the `$strats` command was not being shown in the `$help` list.
* Whole-dollar money amounts _(i.e. those that do not include cents)_ will now truncate the ".00" from the end.

### v0.2.0
#### Functionality
* Users may now bet any amount of money, including non-even amounts and amounts that include cents/decimal places.
* Wallets and other statistics are now saved to a database rather than being stored in memory. Wallet data will be remembered forever if the bot goes offline _(i.e. between updates/crashes)_.
* Changed a few of the interface emoji.
* Changed most messages to embeds instead. this should look nicer and make the chat history easier to grok.
* Bot will no longer delete messages. This will be added again in a later version.
* `$closebets` now shows a list of bets that have been made for easy reference.

#### Back-end changes.
* Replaced the pile of `if` statements with `@client.command()` blocks, making readability and maintenance easier in the future. Nothing should change on the user end.
* Using the internal (albeit less-pretty) `$help` command that comes baked into `commands.Bot()`.

### v0.1.0
* Integrated standing bets into `$closebets` commands
* Made the #blackjack channel more like an app than a chat stream _(the bot will delete messages when no longer relevant)_.
* Created `$blackjack` as an alias of `$pay @user 2.5x`.

## To do
#### Functionality
* Add an option to buy in _(e.g. when a user zeroes out their wallet)_.
* Add an option to change already-placed bets while the table is still open.
* Add avatar thumbnails into the win/loss messages _(tried this before, but the relatively-hacky approach I tried never made it out of testing in v0.2.0)_.

#### Code
* Clean up the god-forgotten mess of sellotaped-together code in `userInDatabase`. Seriously, that function is a mess to look at, even though it works.
* Shorten `isDealer()`.
* Have the bot only watch a certain channel or channels so as to avoid destructive or disruptive behaviour in other channels.
* Move to SQLALchemy instead of using ActiveAlchemy (?).
