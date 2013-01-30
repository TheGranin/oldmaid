from CardHolder import *
from communication import *
import json
import string


# addr = 'njaal.net'
# addr = '129.242.22.237'
addr = 'localhost'
port = 9898


#Update this to handle the connections as well
class Players():
	def __init__(self, players, nick):
		'''
		Since dicts in python is sorted after buckets, it must be sorted correctly again, so here is a hack to complete it
		'''
		self.players = []
		self.out = []
		self.index = 0
		self.nick = nick
		rightOrderOfPlayers = sorted(players)
		
		for player in rightOrderOfPlayers:
			self.players.append(players[player])
			if players[player][-1] == nick:
				self.index = len(self.players) - 1

	

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

		#If not we need to resort the list of players and who we are connected to and such

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





#Main class, should control the game
class Player:
	def __init__(self, nick):
		self.nick = nick
		self.state = "Startphase"
		self.hand = CardHolder()
		self.client = Client()

	#should run the whole game, state machine? METHODS !!!!
	def main(self):

		gameData =  self.joinTheTable()
		while(self.state != "GameOver"):
			if self.state == "Startphase":
				print "State : Startphase"
				# Should parse the data and do an action based on the data, if i am player one i should draw a card, if not i should wait until it's my turn
				# gameData = json.loads('{"result":"ok", "players":{"player1":[["1.1", 11], "asv009"], "player2":[["2.2", 22], "nick"]}}')
				
				if gameData["result"] == "ok":
					self.players = Players(gameData["players"], self.nick)
					
					#MAYBE NOT
					# Start a thread acception connections now, just to make it ready
					# thread.start_new_thread(self.server.connect(),())
					me = self.players.getMyData()

					#NOTE if i use the ip from the table something goes wrong
					self.server = Server('0.0.0.0', me[0][1])

					self.nextPlayer = self.players.getNextPlayer()
					self.client.connect(self.nextPlayer[0][0], self.nextPlayer[0][1])
					self.server.connect()

					
				

					#I am first player, i should start drawing
					if self.players.getMyIndex() == 0:
						self.state = "DrawCardFromTable"

					#I am not first player, i should wait for my turn
					else:
						self.state = "WaitForTurn"

				else:
					print "The table returned error, can't play the game ", gameData 
					return
			elif self.state == "DrawCardFromTable":
				print "State : DrawCard"
				cardData = self.drawCardFromTable()
		
				# message from table can be --> {result:ok/last_card/error, card: [3, spades]}
				# cardData = json.loads('{"result":"ok", "card": ["3", "spades"]}')
				if cardData["result"] != "error":
					
					#Place the card inside your hand if not a pair
					cardtmp = cardData["card"]
					card = Card(cardtmp[0], cardtmp[1])

					if self.hand.equalCards(card):
						discardList = self.hand.discardCardPair(card)
						self.discardCards(discardList, False)
					else:
						self.hand.insertCard(card)

					if cardData["result"] == "ok":
						self.sendTurnToNextOpponent()
						self.state = "WaitForTurn"
					elif cardData["result"] == "last_card":
						self.state = "OfferHand"
		
				else:
					print "Didn't get to draw a card ", cardData
					return 
				
					
				
				
			elif self.state == "WaitForTurn":
				print "State : waiting"
			
				try:
					datafromOponent = json.loads(self.server.recive(1000))
				except Exception as e:
					res = self.players.update(self.getStatus())
					if (res == -1):
						print "I Lost the game, Game over"
						return

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
				#Can win game here
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


				num = random.randint(0,int(datafromOponent["num_cards"]))
				sendPickData = json.dumps({'cmd' : 'pick', 'card_num' : num})
				print "picked : ", num
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
							print "I won the game"
							self.sendOut()
							self.sendOfferHand()
							self.state = "WaitForEndOfGame"
							continue
						
					else:
						self.hand.insertCard(card)

					self.state = "OfferHand"
					self.offerHand()

					#If i took the last card from the other player
					if total == 1:
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
		#TODO Something wrong here
		#TODO fix out message
		print self.hand
		self.hand.shuffle()


		print "length of card ", len(self.hand)
		
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
		print datafromOponent
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
		joinTableData = json.dumps({'cmd': 'join', 'nick': self.nick})
	
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
		
		discardCardData = json.dumps({"cmd": "discard", "cards": str(cards), "last_cards": (len(self.hand) == 0) & test})

		response = self.sendToTable(discardCardData)
		if response["result"] != "ok":
			print "Something went wrong with discard ", response


	def sendToTable(self, data):
		self.tableClient.send(data)
		return json.loads(self.tableClient.recive(1000))



if __name__ == "__main__":
	player = Player(sys.argv[1])
	player.main()



