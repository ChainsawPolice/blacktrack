'''Defines the database model.'''
from active_alchemy import ActiveAlchemy
from btmodules.global_constants import defaultWalletAmount

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

def userInDatabase(userID):
	'''Queries the database for the user. Returns False if they don't exist in the database yet.'''
	for thisUser in User.query().order_by(User.updated_at.desc()).filter(User.dc_uniqueid == int(userID)):
		return thisUser
	return False
