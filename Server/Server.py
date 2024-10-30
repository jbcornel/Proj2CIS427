import socket
import select
import threading
import sqlite3
import sys


SERVER_HOST = '0.0.0.0'
BUFFER_SIZE = 4096

userSessions = {}
dbLock = threading.Lock()

#function to start server and initialize server socket, new client sockets, and reply to I/0 events when
#client sockets are ready to be read from 
def startServer():
    
    #check to make sure command to start server is structured correctly
    if len(sys.argv) != 3:
        print('Error: Server requires Host address and port number passed in command start server ex. python3 Server.py <hostAddresss> <portNumber> ')
        sys.exit(1)

    
    #assign host address and port to input parameters
    hostAddress = sys.argv[1]
    port = int(sys.argv[2])


    #initialize server socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((hostAddress, port))
    serverSocket.listen(10)

    print(f'server listening on {hostAddress}:{port}\n')

    #create global variable to keep track of monitored sockets for the server and initialize with server socket

    global socketList
    socketList = [serverSocket]

    #event loop for scanning sockets to check which are ready to be read from and if they are then process
    # the command for the socket
    while True:
        #list of sockets that are ready to read from socketList
        readableSockets, _, _ = select.select(socketList, [], [])

        #loop through all sockets ready to read
        for readableSocket in readableSockets:

            #if the socket ready to read is the server socket then a new user is trying to connect and we
            #need to initialize the connection with a new socket for the user to use to communicate with the server

            if readableSocket == serverSocket:
                #create new so
                clientSocket, clientAddress = serverSocket.accept()

                socketList.append(clientSocket)
                #add default user data for the new connected user
                userSessions[clientSocket] = {'loggedIn': False, 'username': None, 'userID': None}
                print(f'New Connection from {clientAddress}')
            else:
                    #else the socket that was ready to be read was a clientSocket aka the client had sent a command
                    #and it is ready to be processed in the buffer
                try:
                    
                    msg = readableSocket.recv(BUFFER_SIZE).decode().strip()
                    #if there is no message present in the socket then the connection was closed by the client 
                    if not msg:
                        
                        print(f'Connection closed by {readableSocket.getpeername()}')
                        #remove user session/socket data
                        if readableSocket in socketList:
                            socketList.remove(readableSocket)
                        if readableSocket in userSessions:
                            del userSessions[readableSocket]  
                        readableSocket.close()
                    else:
                        # Process client command
                        handleClientCommand(readableSocket, msg)
                except Exception as e:
                    #processing client request resulted in error, remove the client and close the connection
                    print(f'Error handling message from {readableSocket.getpeername()}: {str(e)}\n')
                    if readableSocket in socketList:
                            socketList.remove(readableSocket)
                    if readableSocket in userSessions:
                            del userSessions[readableSocket]  # Remove session for disconnected socket
                    readableSocket.close()


#create global variable to keep track of monitored sockets for the server and initialize with server socket
global sockets_list
sockets_list = []

#function takes clientSocket, and the command associated with the socket
def handleClientCommand(clientSocket, msg):

    print(f'Received from {clientSocket.getpeername()}: {msg}')

    #conditional statement to decide which command was requested based on message
    #parameters are sent to functions and response is configured and sent and completed in
    # processing functions
    if msg.startswith('LOGIN'):
        handleLOGIN(clientSocket, msg)
    elif msg.startswith('LOGOUT'):
        handleLOGOUT(clientSocket)
    elif msg.startswith('QUIT'):
        clientSocket.send('200 OK: Farewell.\n'.encode())
        print(f'Closing connection with clientSocket: {clientSocket.getpeername()}\n')
        global socketList
        if clientSocket in userSessions:
            del userSessions[clientSocket]
        if clientSocket in socketList:
            socketList.remove(clientSocket)
        clientSocket.close()
    elif msg.startswith("BUY"):
        handleBuy(clientSocket, msg)
    elif msg.startswith("SELL"):
        handleSell(clientSocket, msg)
    elif msg.startswith("BALANCE"):
        handleBalance(clientSocket, msg)
    elif msg.startswith("LIST"):
        handleList(clientSocket, msg)
    else:
        clientSocket.send(f'400 Error: Unknown command received {msg}\n'.encode())



#login functions checks LOGIN credentials with entries in the database, if they match then start new thread,
#change user session data for user
def handleLOGIN(clientSocket, msg):

    with dbLock:
        try:
            _, username, password = msg.split()
            cursor.execute('SELECT * FROM Users WHERE userName = ? AND password = ?', (username, password))

            user = cursor.fetchone()

            if user:
                
                userID, _, firstName, lastName, userName, _, _, isRoot = user

                userSessions[clientSocket] = {

                    'loggedIn': True,
                    'userName': userName,
                    'userID': userID,
                    'isRoot': isRoot
                }
                response = f'200 OK: Logged in as {username}'
                print(f'User {username} logged in. Current userSessions: {[session for session in userSessions.values()]}\n')
            else:
                response = '401 Error: invalid username or password...\n'
        except ValueError:
            response = '403 Message format error: LOGIN needs 2 parameters, username and password...\n'
        clientSocket.send(response.encode())


#login function checks if user is currently logged in and if they are logs them out, then closes
#the connection for the client socket
def handleLOGOUT(clientSocket):

    if clientSocket in userSessions and userSessions[clientSocket]['loggedIn']:
        username = userSessions[clientSocket]['userName']

        userSessions[clientSocket] = {'loggedIn': False, 'userName': None, 'userID': None}
        response = f'200 OK: Logged out user {username} successfully...\n'
        print(f'200 OK: logged out user {username}. Current userSessions: {[session for session in userSessions.values()]}\n')
    else:
        response = '400 Error: user not logged in...\n'
    
    clientSocket.send(response.encode())


if __name__ == '__main__':

    dbConnection = sqlite3.connect('pokemonTrade.db', check_same_thread=False)
    cursor = dbConnection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        firstName TEXT,
        lastName TEXT,
        userName TEXT NOT NULL,
        password TEXT NOT NULL,
        usdBalance REAL NOT NULL,
        isRoot INTEGER NOT NULL DEFAULT 0
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PokemonCards (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        cardName TEXT NOT NULL,
        cardType TEXT NOT NULL,
        rarity TEXT NOT NULL,
        count INTEGER NOT NULL,
        ownerID INTEGER,
        FOREIGN KEY (ownerID) REFERENCES Users(ID)
    )''')

    cursor.execute("SELECT COUNT(*) FROM Users")
    result = cursor.fetchone()
    if result and result[0] == 0:
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('admin@pokemontrade.com', 'Admin', 'User', 'admin', 'adminpassword', 1000.0, 1))
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('john.doe@example.com', 'John', 'Doe', 'johndoe', 'password123', 500.0, 0))
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('jane.smith@example.com', 'Jane', 'Smith', 'janesmith', 'mypassword', 750.0, 0))
        dbConnection.commit()

    # Insert default pokemon cards if not already present
    cursor.execute("SELECT COUNT(*) FROM PokemonCards")
    result = cursor.fetchone()
    if result and result[0] == 0:
        cursor.execute("INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID) VALUES (?, ?, ?, ?, ?)",
                       ('Pikachu', 'Electric', 'Common', 10, 1))
        cursor.execute("INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID) VALUES (?, ?, ?, ?, ?)",
                       ('Charizard', 'Fire', 'Rare', 2, 2))
        cursor.execute("INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID) VALUES (?, ?, ?, ?, ?)",
                       ('Bulbasaur', 'Grass', 'Common', 5, 3))
        dbConnection.commit()


    startServer()