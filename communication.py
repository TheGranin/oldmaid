import socket
import sys
import time
import thread

class Server():
	def __init__(self, addr, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
		print "server listening on addr, port: ", addr, port
		self.sock.bind((addr, port))
		self.sock.listen(8)

	def connect(self):
		print "Start accepting connections"
		try:
			(self.connection, addr) = self.sock.accept()
			print "Client connected", self.connection, addr
		except Exception as e:
			print "Connection error", e.args

		
	def recive(self, length, timeout = None):
		self.connection.settimeout(timeout)
		return self.connection.recv(length)
	def send(self, data):
		self.connection.send(data)
	def close(self):
		self.connection.close()

class Client():
	def connect(self, addr, port):
		print "Client connecting to: ", addr,port
		try:    
			self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.cs.connect((addr, port))
			print "Connection complete"
		except Exception as e:
			print e.args

	def close(self):
		print "SOMETHIGN CLOSED"
		self.cs.close()
	def send(self, data):
		self.cs.send(data)
	def recive(self, length, timeout = None):
		self.cs.settimeout(timeout)
		return self.cs.recv(length)


if __name__ == "__main__":
	if len(sys.argv) == 2:
		print "Start server test"
		server = Server('0.0.0.0', 30689)
		thread.start_new_thread(server.connect, (None, ))
		time.sleep(5)
		print "start reciving"
		try:
			print server.recive(1000)
		except Exception as e:
			print e
			print server.recive(1000)
		print "closing the shit"
		server.recive(1000)
		
	else:
		client = Client()
		client.connect('localhost',30689)
		time.sleep(10)
		client.connect('localhost',30689)
		client.send("mordi")

		client.close()
	



	