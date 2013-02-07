from CardHolder import *
from communication import *
import json
import string


addr = 'njaal.net'
#addr = 'localhost'
port = 9898
my_port = random.randint(10000, 15000)

class Players():
	'''
	Class for keeping track of the players in play
	'''
	def __init__(self, players, nick):
		print players

		self.players = players
		self.out = []
		self.index = 0
		self.nick = nick

		#optimize in the future !!!! can find this faster
		for player in self.players:
			if player[-1] == nick:
				self.index = self.players.index(player)

	def getMyData(self):
		return self.players[self.index]

	def getNextPlayer(self):
		return self.players[(self.index + 1) % len(self.players)]

	def getMyIndex(self):
		return self.index

	def update(self, playersData):
		# If this is the case, it means that the game is over and we have a looser
		if len(playersData["in"]) <= 1:
			return -1

		#If not we need to resort the list of players and who we are to connect to and such

		remove = []
		for player in playersData["out"]:
			for tuples in self.players:
				if tuples[-1] == player:
					remove.append(tuples)

		self.players = [x for x in self.players if x not in remove]

		index = 0
		for player in self.players:
			if player[-1] == self.nick:
				self.index = index
				break
			index += 1
			
		return 0



class Player:
	'''
	Main class to do the old maid
	'''
	def __init__(self, nick):
		self.nick = nick
		self.state = "Startphase"
		self.hand = CardHolder()
		self.client = Client()

	def main(self):

		gameData =  self.joinTheTable()
		while(self.state != "GameOver"):
			if self.state == "Startphase":
				print "State : Startphase"
				
				if gameData["result"] == "ok":

					#Start by connecting to the other players
					self.players = Players(gameData["players"], self.nick)
					me = self.players.getMyData()
					self.server = Server('0.0.0.0', me[0][1])
					

					self.nextPlayer = self.players.getNextPlayer()

					#Nasty hack because the server sucks BIG TIME, could write a better one in my sleep
					self.client.connect(self.nextPlayer[0][0].split(':')[-1], self.nextPlayer[0][1])
					self.server.connect()

					#The first player start drawing card from the table
					if self.players.getMyIndex() == 0:
						self.state = "DrawCardFromTable"

					#The rest wait for their turn
					else:
						self.state = "WaitForTurn"

				else:
					print "The table returned error, can't play the game ", gameData 
					return

			elif self.state == "DrawCardFromTable":
				print "State : DrawCard"
				cardData = self.drawCardFromTable()
			

				if cardData["result"] != "error":
					
					#Place the card inside your hand if not a pair
					cardtmp = cardData["card"]
					card = Card(cardtmp[0], cardtmp[1])

					if self.hand.equalCards(card):
						discardList = self.hand.discardCardPair(card)
						self.discardCards(discardList, False)
					else:
						self.hand.insertCard(card)

					#If ok the turn is passed to the next player
					if cardData["result"] == "ok":
						self.sendTurnToNextOpponent()
						self.state = "WaitForTurn"

					#If last card all the cards has been drawn and i should start offering my hand
					elif cardData["result"] == "last_card":
						self.state = "OfferHand"
		
				else:
					print "Didn't get to draw a card ", cardData
					return 
				
					
			elif self.state == "WaitForTurn":
				print "State : waiting"

				#Do an action based on the cmd recived from opponent
				datafromOponent = json.loads(self.server.recive(1000))
				if datafromOponent["cmd"] == "your_turn":
					self.server.send(json.dumps({"result": "ok"}))
					self.state = "DrawCardFromTable"

				elif datafromOponent["cmd"] == "offer":
					self.server.send(json.dumps({"result": "ok"}))
					self.state = "PickCard"

				else:
					print "Got something i didn't expect from opponent ", datafromOponent
					return

			elif self.state == "OfferHand":
				print "State : OfferHand"
				self.offerHand()

			elif self.state == "PickCard":
				print "State : PickCard"

			
				total =int(datafromOponent["num_cards"])
				print "number of cards got from opponent " , total

				if (total <= 0):
					print "Player to the left is done"
					res = self.players.update(self.getStatus())
					if (res == -1):
						print "I Lost the game, Game over"
						return

					#To handle the special case where the prev player is out i need to offer my hand to the next player 
					self.offerHand()

					#in case if i won the game on the last offer hand
					if self.state != "WaitForEndOfGame":
					#Then wait for a new connection beacuse the previous is out
						self.server.connect()
					continue


				num = random.randint(0,int(datafromOponent["num_cards"] ))
				sendPickData = json.dumps({'cmd' : 'pick', 'card_num' : num})
				try:
					self.server.send(sendPickData)
					responseJson = self.server.recive(1000)
					response = json.loads(responseJson)

				except Exception as e:
					print "Pick Card failed: ", e.args
					return

				if response["result"] != "error":
			
					#Place the card inside your hand if not a pair
					cardtmp = response["card"]
					card = Card(cardtmp[0], cardtmp[1])

					if self.hand.equalCards(card):
						discardList = self.hand.discardCardPair(card)
						self.discardCards(discardList)
						
						if len(self.hand) == 0:
							print "I won the game, by picking the last card i needed"
							self.sendOut()
							print "Sending offer hand to", self.nextPlayer[1]
							
							self.sendOfferHand()
							self.state = "WaitForEndOfGame"
							continue
						
					else:
						self.hand.insertCard(card)

					self.state = "OfferHand"
					self.offerHand()

					#If i took the last card from the other player
					if total == 1:
						#nasty hack, to simply allow tha other client to be out
						time.sleep(1)

						status = self.getStatus()
						res = self.players.update(status)
						if (res == -1):
							print "I Lost the game, Picked the last card from the opponent"
							return

						self.server.connect()


				else:
					print "Didn't get to pick a card ", response
					return 
				
			elif self.state == "WaitForEndOfGame":
				print "Won the game"
				
				try:
					responseJson = self.server.recive(1000, 1)
					response = json.loads(responseJson)
					if response["cmd"] == "offer":
						data = json.dumps({"result":"out"})
						self.server.send(data)

				except Exception as e:
					status = self.getStatus()
					print status

					if self.players.update(status) == -1:
						print "Game Over"
						return

				time.sleep(1)
				
				
			else:
				print "unknown state ", self.state
				return




	def offerHand(self):
		print self.hand
		self.hand.shuffle()


		print "Sending offer hand to palyer: ", self.nextPlayer[1]
		#The player i offered my hand to is out, so need to update the players
		if (self.sendOfferHand() == -1):
			res = self.players.update(self.getStatus())
			if res == -1:
				print "I Lost the game, Game over"
				sys.exit()

			print "Previous player is done, nick:", self.nextPlayer[1]
			nextPlayer = self.players.getNextPlayer()
			print "Connecting to the next player and sending offer hand, nick:" , nextPlayer[1]
			self.nextPlayer = nextPlayer
			self.client.connect(self.nextPlayer[0][0], self.nextPlayer[0][1])
			self.sendOfferHand()

		datafromOponent = json.loads(self.client.recive(1000))
		if datafromOponent["cmd"] == "pick":
			data = json.dumps({'result': 'ok', 'card': self.hand.pickCard(int(datafromOponent["card_num"]) - 1)})
			self.client.send(data)
			
			if len(self.hand) == 0:
					print "I won the game"
					self.sendOut()
					self.state = "WaitForEndOfGame" 
					return

			
			self.state = "WaitForTurn"

		else: 
			print "Strange command recived instead of pick: ", datafromOponent




	def sendOut(self):
		data = json.dumps({"cmd" : "out_of_cards"})
		response = self.sendToTable(data);
		if response["result"] != "ok":
			print "didn't get to end the game", response
			sys.exit()


	def sendOfferHand(self):
		sendOfferHandData = json.dumps({'cmd' : 'offer', 'num_cards' : (len(self.hand))})
		try:
			self.client.send(sendOfferHandData)
			responseJson = self.client.recive(1000)
			response = json.loads(responseJson)
		except Exception as e:
				print "Offer hand failed: ", e.args
				sys.exit()

		if response["result"] != "ok":
			return -1
		return 0

	def sendTurnToNextOpponent(self):
		sendTurnData = json.dumps({'cmd' : 'your_turn'})
		try:
			self.client.send(sendTurnData)
			response = json.loads(self.client.recive(1000))

		except Exception as e:
			print "Could't send next turn to socket ", e.args
			sys.exit()

		if response["result"] != "ok":
			print "next player did not accept the next turn ", response

	def getStatus(self):
		data = json.dumps({'cmd': 'status'})
		return self.sendToTable(data)


	def joinTheTable(self):
		#example ('{"result":"ok", "players":{"player1":[["1.1", 11], "asv009"], "player2":[["2.2", 22], "nick"]}}')
		self.tableClient = Client()
		self.tableClient.connect(addr, port)
		joinTableData = json.dumps({'cmd': 'join', 'nick': self.nick, 'port' : my_port})
	
		gameData = self.sendToTable(joinTableData)
		return gameData

	def drawCardFromTable(self):
		# message from table can be --> {result:ok/last_card/error, card: [3, spades]}

		drawCardData = json.dumps({'cmd': 'draw'})
		cardData = self.sendToTable(drawCardData)
		return cardData

	def discardCards(self, cards, test = True):
		# send {cmd:discard, cards: [[3, spades], [3, clubs]], last_cards:true/false} 
		# Returns {result: ok/error, message:ok/error_message}
		
		discardCardData = json.dumps({"cmd": "discard", "cards": cards, "last_cards": (len(self.hand) == 0) & test})
		print discardCardData
		response = self.sendToTable(discardCardData)
		if response["result"] != "ok":
			print "Something went wrong with discard ", response


	def sendToTable(self, data):
		self.tableClient.send(data)
		return json.loads(self.tableClient.recive(1000))



if __name__ == "__main__":
	player = Player(sys.argv[1])
	player.main()



