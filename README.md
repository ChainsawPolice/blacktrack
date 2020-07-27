# BlackTrack
A bet tracker for webcam games of blackjack.
This bot does not play blackjack; it simply tracks bets for the purpose of the cards being dealt via a webcam sharing session.

## Changelog

### v0.3.4
#### Bug fixes
* Fixed a bug where $pay would pay out the dealer instead of the winner @'ed. Consequently, this would fail if the dealer isn't in the database.
* Fixed a bug where pay-out messages would not show, yet the payment would still be registered to the database.

### v0.3
#### Functionality
* Users may now bet any amount of money, including non-even amounts and amounts that include cents/decimal places.
* Wallets and other statistics are now saved to a database rather than being stored in memory. Wallet data will be remembered forever if the bot goes offline _(i.e. between updates/crashes)_.
* Added an option to buy in. When a user zeroes out their wallet or simply wants more money, the dealer can run `$buyin @user`, tagging the user and adding $100 to their wallet
* Users can now change their bets (so long as betting is still open) by re-running `$bet` with the new amount. this will refund their old bet and bet the new amount.
* Changed a few of the interface emoji.
* Changed most messages to embeds instead. this should look nicer and make the chat history easier to grok.
* Bot will no longer delete messages. This will be added again in a later version.
* `$closebets` now shows a list of bets that have been made for easy reference.
* Whole-dollar money amounts _(i.e. those that do not include cents)_ will now truncate the ".00" from the end, looking a little nicer.

#### Bug fixes
* Fixed a bug where `$balance` wouldn't work sometimes due to the message being deleted too soon.
* Fixed a bug in which creating a new wallet failed _(wallet value was int, not float)_.
* Fixed the bug/oversight where the `$strats` command was not being shown in the `$help` list.

#### Code
* Cleaned up database model.
* The bot will now log all bets to the database for lifetime statistics tracking. A command to check these stats will be coming shortly.
* Whether or not command messages will be deleted is now handled by the `deleteUserMessages` variable. A command will be included shortly to toggle this while the bot is running.
* Replaced the pile of `if` statements with `@client.command()` blocks, making readability and maintenance easier in the future. Nothing should change on the user end.
* Using the internal (albeit less-pretty) `$help` command that comes baked into `commands.Bot()`.

## To do
#### Functionality
* Add avatar thumbnails into the win/loss messages _(tried this before, but the relatively-hacky approach I tried never made it out of testing in v0.2.0)_.
* Test if a plaintext @user has been submitted in $pay instead of a mention/tag.
$ Signal mistyped commands to the user.

#### Code
* Clean up the god-forgotten mess of sellotaped-together code in `userInDatabase`. Seriously, that function is a mess to look at, even though it works.
* Shorten `isDealer()`.
* Have the bot only watch a certain channel or channels so as to avoid destructive or disruptive behaviour in other channels.
* Move to SQLALchemy instead of using ActiveAlchemy (?).
