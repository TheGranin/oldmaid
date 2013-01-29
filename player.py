from CardHolder import *
from communication import *
import json
import string
import thread
import sys

# addr = 'njaal.net'
addr = 'localhost'
port = 9898

class Players():
	def __init__(self, players, nick):
		'''
		Since dicts in python is sorted after buckets, it must be sorted correctly again, so here is a hack to complete it
		'''
		self.players = []
		self.index = 0
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

					nextPlayer = self.players.getNextPlayer()

					self.client.connect(nextPlayer[0][0], nextPlayer[0][1])
					self.server.connect()

					#TODO should connect again if this failed


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
						self.discardCards(discardList)
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
				print self.hand
				self.hand.shuffle()


				print "length of card ", len(self.hand)
				self.sendOfferHand()
				datafromOponent = json.loads(self.server.recive(1000))
				if datafromOponent["cmd"] == "pick":
					data = json.dumps({'result': 'ok', 'card': self.hand.pickCard(int(datafromOponent["card_num"]))})
					self.server.send(data)
					self.state = "WaitForTurn"
				else: #can recive out instead ...
					print "Strange command recived instead of pick: ", datafromOponent




			elif self.state == "PickCard":
				print "State : PickCard"
				print "number of cards got from opponent " , int(datafromOponent["num_cards"])
				num = random.randint(0,int(datafromOponent["num_cards"]))
				sendPickData = json.dumps({'cmd' : 'pick', 'card_num' : num})
				print "picked : ", num
				try:
					self.client.send(sendPickData)
					responseJson = self.client.recive(1000)
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
					else:
						self.hand.insertCard(card)

					self.state = "OfferHand"


				else:
					print "Didn't get to pick a card ", response
					return 
				

				# May need it, but it depends how much interopability that should be supported
			# elif self.state = "WaitForOfferCard"

			else:
				print "unknown state ", self.state
				return


	def sendOfferHand(self):
		sendOfferHandData = json.dumps({'cmd' : 'offer', 'num_cards' : (len(self.hand) -1)})

		try:
			self.client.send(sendOfferHandData)
			responseJson = self.client.recive(1000)
			response = json.loads(responseJson)

		except Exception as e:
				print "Offer hand failed: ", e.args
				sys.exit()

		if response["result"] != "ok":
			print "next player did not accept the next turn ", response

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

	def discardCards(self, cards):
		# send {cmd:discard, cards: [[3, spades], [3, clubs]], last_cards:true/false} 
		# Returns {result: ok/error, message:ok/error_message}
		
		discardCardData = json.dumps({"cmd": "discard", "cards": str(cards), "last_cards": len(self.hand) == 0})
		#print discardCardData


		#TEST SERVER DO NOT SUPPORT
		# response = self.sendToTable(discardCardData)
		# print response
		# return response

	def sendToTable(self, data):
		self.tableClient.send(data)
		return json.loads(self.tableClient.recive(1000))



if __name__ == "__main__":
	player = Player(sys.argv[1])
	player.main()



