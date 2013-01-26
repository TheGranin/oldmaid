from Card import *
from random import shuffle

#  TODO what if the card is invalid, either type or number ?, should check this, but for now ignore
class CardHolder:
	def __init__(self):
		self.cards = []

	def insertCard(self, card):
		self.cards.append(card)

	# may not need
	def insertCards(self, cards):
		for card in cards:
			self.cards.append(card)

	def equalCards(self, cardB):
		for cardA in self.cards:
			if cardA == cardB:
				return True
		return False


	def discardCardPair(self, card):
		tmpCard = self.cards[self.cards.index(card)]
		discardList = [[card.number, card.type] , [card.number, card.type]]
		self.cards.remove(card)
		return discardList

	def shuffle(self):
		shuffle(self.cards)

	def pickCard(self, index):
		return self.cards.pop(index)

	def __getitem__(self, index):
		return self.cards[index]

	def __repr__(self):
		return repr(self.cards)

	def __str__(self):
		string = ""
		for card in self.cards:
			string += " " + str(card)

		return string

	def __len__(self):
		return len(self.cards)

if __name__ == "__main__":
	cardHolder = CardHolder()
	cardHolder.insertCard(Card("2", "hearts"))
	cardHolder.insertCard(Card("3", "hearts"))
	cardHolder.insertCard(Card("4", "hearts"))

	print "\n\tCards in hand: \n\t", cardHolder
	cardHolder.shuffle()
	print "\n\tAfter shuffle \n\t", cardHolder 

	print "\n\tCard at cardHolder[0]\n\t ", cardHolder[0] 

	print "\n\tCard taken from cardHolder[0]\n\t ", cardHolder.pickCard(0)
	print "\t", cardHolder

	print "\n\tDoes a pair exist\n\t", cardHolder.equalCards(Card("2", "diamonds"))

	print "\n\tPair to discard with\n\t", Card(cardHolder[-1].number, "diamonds")
	cardHolder.discardCardPair(Card(cardHolder[-1].number, "diamonds"))

	
	print "\n\tDiscard the pair, left are:\n\t", cardHolder
