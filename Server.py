#!/usr/bin/env python
# -*- coding: utf8 -*- 

import socket, time, json, random
import threading

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
        
class Hand:
    def __init__(self, client):
        self._cards = []
        self._client = client
        
    def addCard(self, card):
        if card in self._cards:
            self._cards.remove(card)
            self._discard(card)
        else:
            self._cards.append(card)
            
    def _discard(self, card):
        if card.color == Kinds.RED:
            colors = Kinds.REDS
        else:
            colors = Kinds.BLACKS
        
        cmd = {"cmd": "discard"}
        if self.numCards() == 0:
            cmd["last_cards"] = True
        else:
            cmd["last_cards"] = False

        cmd["cards"] = [[card.value, color] for color in colors]
        print "Discarding, now I got", self.numCards(), "cards left." 
        #self._client.send(cmd)
        #self._client.read() # The OK-message from server
            
    def getCard(self, num):
        if self.numCards() == 0:
            raise IndexError("No cards on the hand")
            return None
        elif num >= self.numCards():
            raise IndexError("Asked for card %d, highest is %d." % (num, self.numCards()-1))
            return None
        return self._cards.pop(num)
            
    def numCards(self):
        return len(self._cards)
        
    def hasJoker(self):
        if self.getJokerIndex():
            return True
        return False
        
    def getJokerIndex(self):
        for x in range(self.numCards()):
            if self._cards[x].color == Kinds.JOKER:
                return x
        return False
            
    def __len__(self):
        return self.numCards()
        
    def __repr__(self):
        if not self._cards:
            return "The hand is empty"
        else:
            myStr = "The hand has following %d card(s):\n" % self.numCards()
            for card in self._cards:
                myStr += "\t%s\n" % str(card)
            return myStr[:-1]
            


class Server:
    def start(self, port, numPlayers=4):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self._sock.bind(("0.0.0.0", port))
        self._sock.listen(3)
        self._numPlayers = numPlayers
        print "Server is running"
        
        while True:
            print "New game: Waiting for players"
            self.getPlayers()
            self.waitForJoin()
            print "Game is starting"
            self.drawStage()
            self.gameStage()
            print "Game completed"
        
    def getPlayers(self):
        pc = []
        for x in range(self._numPlayers):
            conn, addr = self._sock.accept()
            print "Recieved connection", x
            pc.append(conn)
        print "All connections recieved - game starting"
        self.socks = pc
        
    def waitForJoin(self):
        player_nicks = []
        for player in self.socks:
            cmd = player.recv(1024)
            cmd_dict = json.loads(cmd)
            player_nicks.append(cmd_dict["nick"])
        
        players = {}
        cmd = {"result": "ok"}
        for x in range(len(self.socks)):
            playername = "player" + str(x+1)
            players[playername] = [("localhost", 10055+x), player_nicks[x]]
            
        cmd['players'] = players
        self._players = players
        
        for player in self.socks:
            player.send(json.dumps(cmd))
            
    def drawStage(self):
        kinds = [Kinds.HEARTS, Kinds.SPADES, Kinds.CLUBS, Kinds.DIAMONDS]
        deck = []
        for kind in kinds:
            for x in range(1, 14):
                deck.append(Card(x, kind))
        
        deck.append(Card(0, Kinds.JOKER))
        random.shuffle(deck)
        
        player_turn = 0
        while len(deck) > 0:
            cmd = json.loads(self.socks[player_turn].recv(1024))                
            if cmd["cmd"] == "draw":
                card = deck.pop()
                reply = {"card": [card.value, card.kind]}
                if len(deck) == 0:
                    reply["result"] = "last_card"
                else:
                    reply["result"] = "ok"
                
                print "sending card:", card    
                self.socks[player_turn].send(json.dumps(reply))
                player_turn = (player_turn + 1) % self._numPlayers   
                
            elif cmd["cmd"] == "discard":
                print "Player discarded cards"
                reply = {"result": "ok", "message": "ok"}  
                self.socks[player_turn].send(json.dumps(reply))  
            
        print "Draw stage completed"
        
    def gameStage(self):
        pass
        
if __name__ == '__main__':
    server = Server()
    server.start(9898, 2)
    print "Server terminated"