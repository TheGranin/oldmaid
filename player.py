from CardHolder import *
from communication import *
import json

addr = 'njaal.net'
port = 9898

#Main class, should control the game
class Player:
	def __init__(self, nick):
		self.nick = nick
		self.state = "Startphase"

	#should run the whole game, state machine?
	def main(self):

		if (self.state == "Startphase"):
			self.joinTheTable()
			


	def joinTheTable(self):
		self.tableClient = Client()
		self.tableClient.connect(addr, port)
		joinTableData = json.dumps({'cmd': 'join', "nick": self.nick})
		self.tableClient.send(joinTableData)
		gameData = json.load(self.tableClient.recive())




if __name__ == "__main__":
	player = Player("asv009")
	# player.joinTheTable()


