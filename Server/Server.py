
import sqlite3
import sys
import threading
import socket
import select



SERVER_HOST = '0.0.0.0'
SERVER_PORT = 7417
BUFFER_SIZE = 4096


userSessions={}
class ServerConnection:

    def __init__(self, clientSocket, address):
        self.clientSocket = clientSocket
        self.address = address
        self.loggedIn = False
        print(f"New Connection from {address}")

    def fileno(self):
        return self.clientSocket.fileno()
    
    def onread(self):

        try:
            msg = self.clientSocket.recv(BUFFER_SIZE).decode()
            if not msg:
                print(f'client {self.address} disconnected...')
                self.closeConnection()
                
            else:
                print(f'Received from {self.address}: {msg}')
                self.processCommand(msg)
        except Exception as e:
            print(f'Error handling message from {self.address}: {e}')

            self.clientSocket.close()
    

    def processCommand(self, msg):

        if msg.startswith('LOGIN') and self.loggedIn == True:
            self.clientSocket.send(f'400 Error: client user already logged in')
        if msg.startswith('LOGIN') and self.loggedIn != True:
            
            
            segments = msg.split(' ', 2)
            username = segments[1].strip()
            password = segments[2].strip()
            print(username)
            print(password)
            loginStatus = self.checkLogin(username, password)
            print(loginStatus)
            if loginStatus == True:
                self.clientSocket.send(f'200 OK: Logged in successfully {username}\n'.encode())
                self.loggedIn = loginStatus
                clientThread = threading.Thread(target=self.handleClient)
                clientThread.daemon = True
                clientThread.start()
            else:
                self.clientSocket.send(f'401 Invalid username or password...\n'.encode())
        elif msg.startswith('BUY'):
            response = self.processBUY(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('SELL'):
            response = self.processBUY(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('LIST'):
            response = self.processBUY(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('BALANCE'):
            response = self.processBUY(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('DEPOSIT'):
            response = self.processBUY(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('LOOKUP'):
            response = self.processLOOKUP(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('WHO'):
            response = self.processWHO(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('LOGOUT'):
            response = self.processLOGOUT(msg)
            self.clientSocket.send(response.encode())
        elif msg.startswith('QUIT'):
            self.clientSocket.send('200 OK: farewell...\n'.encode())
            self.closeConnection()
        elif msg.startswith('SHUTDOWN'):
            #response = self.processSHUTDOWN(msg)
            #self.clientSocket.send(response.encode())
            x= 10
        else:
            self.clientSocket.send('400 Error: Unknown command {msg}\n'.encode())
    


    
    def handleClient(self):


        while True:

            try:

                msg = self.clientSocket.recv(BUFFER_SIZE).decode().strip()
                if not msg:
                    break
                print(f'Received from client {self.address}: {msg}')

                self.processCommand(msg)
            except:
                print('Error in client handler: {e}')
                break
       
        self.closeConnection()




    def checkLogin(self, username, password):

        dbConnection = sqlite3.connect('pokemonTrade.db')
        cursor = dbConnection.cursor()
        cursor.execute(f"SELECT * FROM Users WHERE userName = '{username}' AND password = '{password}'")
        user = cursor.fetchone()
        print(user)

        if user:
            print(f'user: {user}')
            userID, _, firstName, lastName, userName, _, _, isRoot = user
                   
            userSessions[self.clientSocket] = {'userID': userID, 'userName': userName, 'isRoot': isRoot, 'clientAddress': self.address}
            print(userSessions[self.clientSocket])
            return True
        else:
            print('no user found')
            return False


    def closeConnection(self):
        print(f'Closing connection to {self.address}')
        eventLoop.removeReader(self)
        self.clientSocket.close()
        


        
class Server:
    def __init__(self, host, port):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #???
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((host,port))
        self.serverSocket.listen(10)
        print(f'Server listening on port {port}\n')




    def fileno(self):
        return self.serverSocket.fileno()
    

    def onread(self):

        clientSocket, address = self.serverSocket.accept()
        newConnection = ServerConnection(clientSocket, address)
        eventLoop.addReader(newConnection)


class EventLoop:

    def __init__(self):
        self.readers = []


    def addReader(self, reader):
        self.readers.append(reader)
    

    def removeReader(self, reader):
        if reader in self.readers:
            self.readers.remove(reader)


    def runForever(self):

        while True:
            readers, _, _ = select.select(self.readers, [], [])

            for reader in readers:
                reader.onread()


def createUsersTable(serverSocket):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            firstName TEXT,
            lastName TEXT,
            userName TEXT NOT NULL UNIQUE,
            password TEXT,
            usdBalance REAL NOT NULL,
            isRoot INTEGER NOT NULL DEFAULT 0
            );
        ''')

        dbConnection.commit()
        print("Users table created in sqlite.")
    except Exception as e:
        print(f"Failed to create table: {e}, shutting down server")
        dbConnection.close()
        serverSocket.close()
        sys.exit(1)


def createPokemonCardsTable(serverSocket):

    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PokemonCards (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        cardName TEXT NOT NULL,
        cardType TEXT NOT NULL,
        rarity TEXT NOT NULL,
        count INTEGER,
        ownerID INTEGER,
        FOREIGN KEY (ownerID) REFERENCES Users(ID)
        );
        ''')
        
        dbConnection.commit()
        print("PokemonCards table created in sqlite.")
    except Exception as e:
        print(f"Failed to create table: {e}, shutting down server")
        dbConnection.close()
        serverSocket.close()
        sys.exit(1)














def createDefaultUsers(): 
    
    cursor.execute("SELECT COUNT(*) FROM Users")
    userCount = cursor.fetchone()[0]
    print(f"currentUserCount: {userCount}")

    if userCount == 0:
        cursor.execute('''
        INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot)
        VALUES(?,?,?,?,?,?,?)
        ''', ("admin@pokemontrade.com" , "Joseph" , "Cornell" , "admin" , "adminpassword" , 100.0 , 1)
        )
        cursor.execute('''
        INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot)
        VALUES(?,?,?,?,?,?,?)
        ''', ("secondUser@poketrade.com" , "userTwoFirstName" , "userTwoLastName" , "userTwo" , "userTwoPassword" , 100.0 , 0)
        )
        dbConnection.commit()
        print(
f'''default user created
email: admin@poketrade.com
firstName: Joseph
lastName: Cornell
userName: admin
password: adminpassword
usdBalance: 100.0
ID: 1
                 ''')
        print(
f'''default user created
email: secondUser@poketrade.com
firstName: userTwoFirstName
lastName: userTwoLastName
userName: userTwo
password: userTwoPassword
usdBalance: 100.0
ID: 2
                 ''')





def createDefaultCards():
    
    cursor.execute("SELECT COUNT(*) FROM PokemonCards")
    cardCount = cursor.fetchone()[0]
    
    

    if cardCount == 0:
        cursor.execute('''
        INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID)
        VALUES(?,?,?,?,?)
        ''', ("BULBASAUR", "GRASS", "COMMON", 3 , 1)
        )
        cursor.execute('''
        INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID)
        VALUES(?,?,?,?,?)
        ''', ("SQUIRTLE", "WATER", "COMMON", 3 , 1)
        )
        dbConnection.commit()
        print(f'''default cards created
                
                 ''')

def testDB():


    cursor.execute(f"SELECT ID, cardName, cardType, rarity, count, ownerID FROM PokemonCards WHERE ownerID = 1")
    cards = cursor.fetchall()
    response = 'printing all default entries in pokemon card table: \n'
    for card in cards:

        response += f"{card[0]} {card[1]} {card[2]} {card[3]} {card[4]} {card[5]}\n"

    print(response)

if __name__ == '__main__':

    if len(sys.argv) != 3:
        print('Usage: python Server.py <host> <port>')
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    dbConnection = sqlite3.connect('pokemonTrade.db', check_same_thread= False)
    cursor = dbConnection.cursor()

    server = Server(host, port)
    createUsersTable(server.serverSocket)
    createPokemonCardsTable(server.serverSocket)
    createDefaultUsers()
    createDefaultCards()
    testDB()

    eventLoop = EventLoop()
    eventLoop.addReader(server)

   
    

    eventLoop.runForever()





# try:
#     #connecting server and client socket
#     serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     serverSocket.bind((SERVER_HOST, SERVER_PORT))
#     serverSocket.listen(10)  # Listen for up to 10 connections simultaneously
#     print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")
# except Exception as e:
#     print(f"Failed to initialize server socket: {e}")
#     sys.exit(1)












# def processWho()



# def processLOGIN(commandParameters, clientSocket):
    
#     if len(commandParameters) != 2:
#         return '403 Message format error: LOGIN command requires 2 case-sensitive parameters ref. username, password \n ex. LOGIN username password\n'
    
#     username, password = commandParameters
#     cursor.execute(f"SELECT * FROM Users WHERE userName = '{username}' AND password = '{password}'")
#     user = cursor.fetchone()
#     print(user)



#     if user:
#         print(f'user: {user}')
#         userID, _, firstName, lastName, userName, _, _, isRoot = user
#         ClientAddress = clientSocket.getpeername()[0]
                   
#         userSessions[clientSocket] = {'userID': userID, 'userName': userName, 'isRoot': isRoot, 'clientAddress': ClientAddress}
#         print(userSessions[clientSocket])
#         return f'200 OK\n'
#     else:
#         return 


def processBUY(commandParameters):
    x=10


def processSELL(commandParameters):
    x=10
    


def processLIST(commandParameters):
    x=10





def processBALANCE(commandParameters):
    x=10

def processSHUTDOWN(commandParameters):
    x=10

def processLOGOUT():
    x=10


# def processCommand(segments, clientSocket):


#     clientCommand = segments[0].upper()
#     print(clientCommand)
    
#     commandParameters = segments[1:]
#     print(commandParameters)

#     if clientCommand == 'LOGIN' or clientCommand == 'QUIT':

#         if clientCommand == 'LOGIN':
            
#             response = processLOGIN(commandParameters, clientSocket)
        
#         elif clientCommand == 'QUIT':

#            # response = processQUIT()
#            x=10
#     else:

#         if clientSocket not in userSessions:
#             return '401 Unauthorized command error: Please Login first...'
#         if clientCommand=='BUY':
        
#             response = processBUY(commandParameters)

#         elif clientCommand =='SELL':
            
#             response = processSELL(commandParameters)
            
#         elif clientCommand =='LIST':
            
#             response = processLIST(commandParameters)

        
#         elif clientCommand =='BALANCE':
            
#             response = processBALANCE(commandParameters)

#         elif clientCommand == 'LOGOUT':

#             response = processLOGOUT()

#         elif clientCommand =='SHUTDOWN':
#             response = processSHUTDOWN()

#     return response

    

# def processClient(clientSocket, clientAddress):

#     while True:

#         try:
#             request = clientSocket.recv(BUFFER_SIZE).decode().strip()
#             if not request: 


#                 print(f"Connection closed by {clientAddress}")
#                 break

#             print(f"Received by client {clientAddress}: {request}")

#             segments = request.split()
#             response = processCommand(segments, clientSocket)
#             clientSocket.send(response.encode())
#         except Exception as e:
#             print(f"Error handling client request: {e}")
#             break
    
#     clientSocket.close()

# def startServer():

#     createUsersTable()
#     createPokemonCardsTable()
#     createDefaultUsers()
#     createDefaultCards()
#     testDB()


#     while True:

#         #List of sockets that have data in buffer ready to read, then two throwaway variables
#         # to fill the return subsets of the writeable list and exceptional condition list 
#         readableSockets, _, _ = select.select([serverSocket] + list(userSessions.keys()), [], [])

#         for socket in readableSockets:
            
#             if socket == serverSocket:
               
#                 try:
#                     clientSocket, clientAddress = serverSocket.accept()
#                     print(f'New client connected... {clientAddress}\n')
#                     clientThread = threading.Thread( target=processClient, args=(clientSocket, clientAddress))
#                     clientThread.start()

#                 except Exception as e:
#                     print(f"Error accepting connection {e}\n")
#                     break
#             else:
#                 processLOGIN(socket)
                
            
#     serverSocket.close()
#     dbConnection.close()







# if __name__ == '__main__':
#     startServer()
