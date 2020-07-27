''' Commonly-used utilities shared among modules '''

# Formats floats as currency.
def asMoney(value):
	if float(value).is_integer():
		return "${:,.0f}".format(value)
	else:
		return "${:,.2f}".format(value)
