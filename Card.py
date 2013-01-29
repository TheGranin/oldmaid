import sys
class Kinds:
    HEARTS  = "hearts"
    SPADES   = "spades"
    CLUBS    = "clubs"
    DIAMONDS = "diamonds"
    JOKER    = "joker"
    
    RED      = "red"
    BLACK    = "black"
    
    REDS     = [HEARTS, DIAMONDS]
    BLACKS   = [CLUBS,  SPADES]
    ALL = [HEARTS, DIAMONDS, CLUBS,  SPADES, JOKER]

class Card:
	def __init__(self, number, type):
		if not type.lower() in Kinds.ALL:
			print "Type not supported"
			sys.exit()

		self.type = type.lower()
		self.number = int(number)

	def __eq__(self, card):
		if self.type in Kinds.REDS and card.type in Kinds.REDS:
		 		if self.number == card.number:
					return True

		if self.type in Kinds.BLACKS and card.type in Kinds.BLACKS:
			if self.number == card.number:
					return True

		return False

	def __repr__(self):
		return [self.number, self.type]

	def __str__(self):
		return str([self.number, self.type])



if __name__ == "__main__":
	card = Card("2", "hearts")
	print card

	card2 = Card("2", "diamonds")
	card3 = Card("2", "spades")
	print card == card2
	print card == card3

	card4 = Card("2", "clubs")
	print card4 == card3