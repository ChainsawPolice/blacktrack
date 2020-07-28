'''Defines the database model.'''
from active_alchemy import ActiveAlchemy
from btmodules.global_constants import defaultWalletAmount
import json

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
	was_a_win = db.Column(db.Boolean)

def userInDatabase(userID):
	'''Queries the database for the user. Returns False if they don't exist in the database yet.'''
	query = User.query().order_by(User.updated_at.desc()) # Query the user table, sorting by last updated, and store the results in a list.
	for thisUser in query.filter(User.dc_uniqueid == int(userID)):
		return thisUser
	return False

def largestBet(userID):
	betsByUser = []
	query = Bets.query().order_by(Bets.bet_amount.desc())
	for thisBet in query.filter(Bets.bet_user_id == int(userID)):
		betsByUser.append(thisBet)

	if betsByUser[0].was_a_win == True:
		winState = ' (win)'
	elif betsByUser[0].was_a_win == False:
		winState = ' (loss)'
	elif betsByUser[0].was_a_win == None:
		winState = ''
	return {
		'wasAWin'   : winState,
		#'bet_user_id' : gggggggggg,
		'betTime'   : betsByUser[0].created_at.format('D MMMM [\']YY [@] h:MM A'),
		'betAmount' : betsByUser[0].bet_amount
	}

def initDatabase():
	db.create_all()
