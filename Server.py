# -*- coding: utf8 -*- 

import socket, time, json, random, sys
import thread

class Kinds:
    HEARTS   = "hearts"
    SPADES   = "spades"
    CLUBS    = "clubs"
    DIAMONDS = "diamonds"
    JOKER    = "joker"
    
    RED      = "red"
    BLACK    = "black"
    
    REDS     = [HEARTS, DIAMONDS]
    BLACKS   = [CLUBS,  SPADES]
    
class Player:
    def __init__(self, nick, conn):
        self.nick = nick
        self.conn = conn
        self.ip = None
        self.out = False
        self.myTurn = False
        self.nextPlayer = None
        
    def setOut(self):
        self.out = True
        
    def nextPlayerTurn(self):
        if self.myTurn:
            self.myTurn = False
            self.nextPlayer.myTurn = True
    
class Card:
    def __init__(self, number, kind):
        self.value = number
        self.kind = kind
        
    @property
    def color(self):
        if self.kind in Kinds.BLACKS:
            return Kinds.RED
        elif self.kind in Kinds.REDS:
            return Kinds.BLACK
        elif self.kind == Kinds.JOKER:
            return Kinds.JOKER
        else:
            raise Exception("Invalid card kind: Card has no color")
        
    def __eq__(self, other):
        if self.color == other.color and self.value == other.value:
            return True
        return False
        
    def __repr__(self):
        if self.kind == Kinds.JOKER:
            return "The joker"
        return "%s of %s" % (self.value, self.kind)
        
class Server:
    def __init__(self, port, numplayers=4):
        self._maxPlayers = numplayers
        self._port = port
        
    def start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self._sock.bind(("0.0.0.0", self._port))
        self._sock.listen(3)
    
        print "Server started..."
        while True:
            try:
                print "Waiting for players connect."
                players = self.getPlayers()
                print "All players connected: Starting game!"
                self.startNewGame(players)
                
            except KeyboardInterrupt:
                print "Server shutting down"
                return
            except Exception as e:
                print "Error starting game... Error:", e
                            
    def startNewGame(self, players):
        deck = []
        for color in Kinds.REDS + Kinds.BLACKS:
            for x in range(1, 14):
                deck.append(Card(x, color))
        deck.append(Card(1, Kinds.JOKER))
        random.shuffle(deck)
        
        for player in players:
            thread.start_new_thread(self._playerThread, (deck, player, players))
        
    def _playerThread(self, deck, player, players):
        while True:
            try:
                msg = player.conn.recv(1024)
                cmd = json.loads(msg)
            
                if cmd["cmd"] == "status":
                    print "Recieved status message from", player.nick
                    outPlayers = [p.nick for p in players if p.out]
                    inPlayers = [p.nick for p in players if not p.out]
                    reply = {"in": inPlayers, "out": outPlayers}
                    player.conn.send(json.dumps(reply))              
                                        
                elif cmd["cmd"] == "out_of_cards":
                    print player.nick, "is out."
                    player.setOut()
                    player.conn.send(json.dumps({"result": "ok"}))
                    
                elif cmd["cmd"] == "discard":
                    print player.nick, "Discarded cards"
                    player.conn.send(json.dumps({"result": "ok", "message": "ok"}))
                    
                elif cmd["cmd"] == "draw":
                    if not player.myTurn:
                        print player.nick, "tried to cheat!"
                        player.conn.send(json.dumps({"result": "error"}))
                    else:
                        card = deck.pop(0)
                        print player.nick, "draws card:", card
                        reply = {"card": [card.value, card.kind]}
                        if len(deck) == 0:
                            reply["result"] = "last_card"
                            print "This is the last card -> GAME STARTING"
                        else:
                            reply["result"] = "ok"
                        player.nextPlayerTurn()    
                        player.conn.send(json.dumps(reply))
            except Exception as e:
                print "Closing connection to client:", player.nick
                return
            
    def getPlayers(self):
        players = []
        for x in range(self._maxPlayers):
            conn, addr = self._sock.accept()
            player = Player("NoName", conn)
            player.ip = addr[0]
            print "A player joined the game"
            players.append(player)
        self.waitForJoin(players)
        
        for x in range(len(players)):
            players[x].nextPlayer = players[(x+1)%len(players)]
        players[0].myTurn = True
        return players
        
    def waitForJoin(self, players):
        player_nicks = []
        for player in players:
            cmd = player.conn.recv(1024)
            cmd_dict = json.loads(cmd)
            player.nick = cmd_dict["nick"]
            
            if "steffen" in player.nick.lower():
                cmd = {"result": "error", "message": "Awsomeness of name too high! (it's over 9000)"}
                player.conn.send(json.dumps(cmd))
                raise Exception("Too awsome name used!")
        
        player_dict = {}
        cmd = {"result": "ok"}
        start_port = random.randrange(20000, 30000)
        for x in range(len(players)):
            playername = "player" + str(x+1)
            player_dict[playername] = [(players[x].ip, start_port+x), players[x].nick]
            
        cmd['players'] = player_dict        
        for player in players:
            player.conn.send(json.dumps(cmd))

if __name__ == '__main__':
    server = Server(9898, int(sys.argv[1]))
    server.start()
    print "Server terminated"
        