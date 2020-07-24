# BlackTrack
A bet tracker for webcam games of blackjack.

## Changelog
### v0.2.0 (live)
#### Functionality
* Users may now bet any amount of money, including non-even amounts and amounts that include cents/decimal places.
* Wallets and other statistics are now saved to a database rather than being stored in memory. Wallet data will be remembered forever if the bot goes offline _(i.e. between updates/crashes)_.
* Changed a few of the interface emoji.
* Changed most messages to embeds instead. this should look nicer and make the chat history easier to grok.
* Bot will no longer delete messages. This will be added again in a later version.

#### Back-end changes.
* Replaced the pile of `if` statements with `@client.command()` blocks, making readability and maintenance easier in the future. Nothing should change on the user end.
* Using the internal (albeit less-pretty) `$help` command that comes baked into `commands.Bot()`.

### v0.1.0
* Integrated standing bets into `$closebets` commands
* Made the #blackjack channel more like an app than a chat stream _(the bot will delete messages when no longer relevant)_.
* Created `$blackjack` as an alias of `$pay @user 2.5x`.

## To do
#### Functionality
* Log all bets to the database for lifetime statistics tracking.
* Add an option to buy in (e.g. when a user zeroes out their wallet).
* Add an option to change already-placed bets while the table is still open.
* Add avatar thumbnails into the win/loss messages (tried this before, but the relatively-hacky approach I tried never made it out of testing in v0.2.0).
* Make bot delete messages.

#### Code
* Clean up the god-forgotten mess of sellotaped-together code in `userInDatabase`. Seriously, that function is a mess to look at, even though it works.
* Shorten `isDealer()`.
