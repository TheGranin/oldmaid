class Card:
	def __init__(self, number, type):
		self.type = type.lower()
		self.number = number

	def __eq__(self, card):
		if self.type == "hearts" and card.type == "diamonds":
		 		if self.number == card.number:
					return True

		if self.type =="spades" and card.type == "clubs":
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
	card3 = Card("2", "spade")
	print card == card2
	print card == card3