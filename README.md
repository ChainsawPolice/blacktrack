# BlackTrack
A bet tracker for webcam games of blackjack.
This bot does not play blackjack; it simply tracks bets for the purpose of the cards being dealt via a webcam sharing session.






## Changelog
### v0.4
#### Functionality
* Added avatar thumbnails into the win/loss messages _(tried this before, but the relatively-hacky approach I tried never made it out of testing in v0.2.0)_.
* Added the `$stats` command.
* The bot will only listen to two channels, the #blackjack-bot-test channel and the #blackjack channel, so as to avoid `$openbets` getting rid of any messages in proper chats.

#### Bug fixes
* Finally fixed the `$doubleup` and `$split` command _(code was ported incorrectly from v0.2 to v0.3)_.

#### Code
* Started slowly splitting the project into smaller, more easily-maintainable modules.
* Added support for tracking if a bet was a win or a loss for future statistics retrieval. Will implement later.


## To do
#### Functionality
* Signal mistyped commands to the user without stopping console tracebacks.
* Allow dealer to toggle command deletion.
* Add config file.
* Add Lex's command.
* Add `$insurance` – like `$doubledown`, but make it 1.5x.
* Payout messages now show the winnings only, not the entire amount paid out _(e.g. on a bet of $50, the win message now shows that the user won $50 instead of them being paid $100)_.
<!-- * Test if a plaintext @user has been submitted in $pay instead of a mention/tag. -->

#### Code
* Clean up the god-forgotten mess of sellotaped-together code in `userInDatabase`. Seriously, that function is a mess to look at, even though it works.
* Shorten `isDealer()`.
* Have the bot only watch a certain channel or channels so as to avoid destructive or disruptive behaviour in other channels.
* Move to SQLALchemy instead of using ActiveAlchemy (?).
* Further isolate the pay-out code to one common function between `$pay`, `$blackjack`, `$bust`, and `$push`.



9194 4122
