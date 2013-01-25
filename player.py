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
		

	#should run the whole game, state machine?
	def main(self):

		

		#UNCOMMENT WHEN THE SERVER IS UP
		gameData =  self.joinTheTable()
		while(self.state != "GameOver"):
			if self.state == "Startphase":

				# Should parse the data and do an action based on the data, if i am player one i should draw a card, if not i should wait until it's my turn
				# gameData = json.loads('{"result":"ok", "players":{"player1":[["1.1", 11], "asv009"], "player2":[["2.2", 22], "nick"]}}')
				
				if gameData["result"] == "ok":
					self.players = Players(gameData["players"], self.nick)
					
					#MAYBE NOT
					# Start a thread acception connections now, just to make it ready
					# thread.start_new_thread(self.server.connect(),())
					me = self.players.getMyData()
					self.server = Server(me[0][0], me[0][1])

					nextPlayer = self.players.getNextPlayer()

					print "me and nextplayer: ",  me, nextPlayer
					self.client.connect(nextPlayer[0][0], nextPlayer[0][1])
					self.server.connect()

					#should connect again if this failed


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
				print "State is DrawCard"
				# REMOVE when server is up
				cardData = self.drawCardFromTable()

				# message from table can be --> {result:ok/last_card/error, card: [3, spades]}
				# cardData = json.loads('{"result":"ok", "card": ["3", "spades"]}')
				if cardData["result"] == "ok":
					cardtmp = cardData["card"]
					card = Card(cardtmp[0], cardtmp[1])
					if self.hand.equalCards(card):
						discardList = self.hand.discardCardPair(card)
						print "must discard card pair", card
						# print discardList
						self.discardCards(discardList)
					else:
						self.hand.insertCard(card)
						print "My hand is now ", self.hand
					
					self.sendTurnToNextOpponent()
					self.state = "WaitForTurn"

				else:
					print "Didn't get to draw a card ", cardData
			elif self.state == "WaitForTurn":
				"State Is waiting"
			
				datafromOponent = json.loads(self.server.recive(1000))
				if datafromOponent["cmd"] == "your_turn":
					self.server.send(json.dumps({"result": "ok"}))
					self.state = "DrawCardFromTable"

				else:
					print "Got something i didn't expect from opponent ", datafromOponent
					return

			else:
				print "unknown state ", self.state
				return


				

	def sendTurnToNextOpponent(self):
		sendTurnData = json.dumps({'cmd' : 'your_turn'})
		try:
			self.client.send(sendTurnData)
			response = json.loads(self.client.recive(1000))

		except Exception as e:
			print "Could't send data to socket ", e.args

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
		print "Draw card: ", cardData
		return cardData

	def discardCards(self, cards):
		# send {cmd:discard, cards: [[3, spades], [3, clubs]], last_cards:true/false} 
		# Returns {result: ok/error, message:ok/error_message}

		discardCardData = json.dumps({"cmd": "discard", "cards": cards, "last_cards": len(self.hand) == 0})
		print discardCardData


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
	# player.joinTheTable()


