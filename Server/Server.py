from http import client
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
            try:
                if readableSocket == serverSocket:
                #create new socket
                    clientSocket, clientAddress = serverSocket.accept()

                    socketList.append(clientSocket)
                #add default user data for the new connected user
                    userSessions[clientSocket] = {'loggedIn': False, 'username': None, 'userID': None}
                    print(f'New Connection from {clientAddress}...')
                else:
                    msg = readableSocket.recv(BUFFER_SIZE).decode().strip()
                    if not msg:
                        print(f'Connection closed by {readableSocket.getpeername()}...')
                        quit(readableSocket)
                    else:
                        clientCommand(readableSocket, msg, serverSocket)
            except OSError as e:
            # Handle socket errors
                if readableSocket in socketList:
                    print(f'Error handling message from {readableSocket}: {str(e)}')
                    quit(readableSocket)

#create global variable to keep track of monitored sockets for the server and initialize with server socket
global sockets_list
sockets_list = []
#disconnets the client socket from the server socket
def disconnect(clientSocket):
    print(f'Connection closed by {clientSocket.getpeername()}')
    if clientSocket in socketList:
        socketList.remove(clientSocket)
    if clientSocket in userSessions:
        del userSessions[clientSocket]
    clientSocket.close()

#function takes clientSocket, and the command associated with the socket
def clientCommand(clientSocket, msg, serverSocket):
    global socketList

    if clientSocket not in socketList:
        print(f'Socket {clientSocket} is no longer valid, ignoring command.')
        return

    try:
        print(f'Received from {clientSocket.getpeername()}: {msg}')

        if msg.startswith('QUIT'):
            quit(clientSocket)
            return

    #conditional statement to decide which command was requested based on message
    #parameters are sent to functions and response is configured and sent and completed in
    # processing functions
        if msg.startswith('LOGIN'):
            LOGIN(clientSocket, msg)
        elif msg.startswith('LOGOUT'):
            LOGOUT(clientSocket)
        elif msg.startswith('QUIT'):
            clientSocket.send('200 OK: Farewell.\n'.encode())
            print(f'Closing connection with clientSocket: {clientSocket.getpeername()}\n')
            disconnect(clientSocket)
        elif msg.startswith("BUY"):
            buy(clientSocket, msg)
        elif msg.startswith("SELL"):
            sell(clientSocket, msg)
        elif msg.startswith("BALANCE"):
            balance(clientSocket, msg)
        elif msg.startswith("LIST"):
            List(clientSocket)
        elif msg.startswith("LOOKUP"):
            Lookup(clientSocket, msg)
        elif msg.startswith("DEPOSIT"):
            deposit(clientSocket, msg)
        elif msg.startswith("WHO"):
            who(clientSocket, msg)
        elif msg.startswith("SHUTDOWN"):
            shutdown(clientSocket, serverSocket)
        else:
            clientSocket.send(f'400 Error: Unknown command received {msg}\n'.encode())

    except OSError as e:
        print(f'Error handling message from {clientSocket}: {str(e)}')
        quit(clientSocket)

#login functions checks LOGIN credentials with entries in the database, if they match then start new thread,
#change user session data for user
def LOGIN(clientSocket, msg):

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
def LOGOUT(clientSocket):

    if clientSocket in userSessions and userSessions[clientSocket]['loggedIn']:
        username = userSessions[clientSocket]['userName']

        userSessions[clientSocket] = {'loggedIn': False, 'userName': None, 'userID': None}
        response = f'200 OK: Logged out user {username} successfully...\n'
        print(f'200 OK: logged out user {username}. Current userSessions: {[session for session in userSessions.values()]}\n')
    else:
        response = '400 Error: user not logged in...\n'
    
    clientSocket.send(response.encode())

#buy function checks if user is logged in and allows the user to buy Pokemon Cards
#also checks for errors, such as not enough balance
def buy(clientSocket, msg):
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to buy cards\n".encode())
        return

    with dbLock:
            try:
                _, cardName, cardType, rarity, price, count = msg.split()
                price = float(price)
                count = int(count)
                ownerID = session['userID']

                cursor.execute("SELECT usdBalance FROM Users WHERE ID=?", (ownerID,))

                user = cursor.fetchone()
                
                if not user:
                    return "404 User does not exist\n"
                if user:
                #Gets the balance for respective user and executes transaction
                    user_balance = user[0]
                    total_cost = price * count
                    # Check if the user has enough balance
                    if user_balance < total_cost:
                        response = ("402 Not enough balance\n")
                    else:
                    #Subtract cost of new cards and add card to users record
                        new_balance = user_balance - total_cost
                        cursor.execute("UPDATE Users SET usdbalance=? WHERE ID=?", (new_balance, ownerID))
                        cursor.execute("INSERT INTO PokemonCards (cardName, cardType, rarity, count, ownerID) VALUES (?, ?, ?, ?, ?)",
                        (cardName, cardType, rarity, count, ownerID))
                    
                        response = f"200 OK\nBOUGHT: New balance: {count} {cardName}. User USD balance ${new_balance:.2f}\n"
                        print(f'Balance updated')

            except ValueError:
                response = '403 Message format error...\n'
            clientSocket.send(response.encode())

#Sell function checks if user is logged in and allows the user to sell Pokemon Cards
#also checks for errors, such as not enough cards
def sell(clientSocket, msg):
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to sell cards\n".encode())
        return
    
    with dbLock:
            try:
                _, cardName, count, price = msg.split()
                price = float(price)
                count = int(count)
                ownerID = session['userID']

                cursor.execute("SELECT usdBalance FROM Users WHERE ID=?", (ownerID,))

                user = cursor.fetchone()
                
                if not user:
                    return "404 User does not exist\n"
                if user:
                #Gets the balance for respecive user and executes transaction
                    user_balance = user[0]
                    
                    cursor.execute("SELECT count FROM PokemonCards WHERE cardName=? AND ownerID=?", (cardName, ownerID))
                    card = cursor.fetchone()
                    if not card or card[0] < count:
                        response =  "404 Not enough cards to sell or card does not exist\n"
                    else:
                        sale_value = price * count
                        cursor.execute("UPDATE Users SET usdBalance = usdBalance + ? WHERE ID = ?", (sale_value, ownerID))
                        new_count = card[0] - count

                        if new_count == 0:
                            cursor.execute("DELETE FROM PokemonCards WHERE cardName=? AND ownerID=?", (cardName, (ownerID)))
                        else:
                            cursor.execute("UPDATE PokemonCards SET count=? WHERE cardName=? AND ownerID=?", (new_count, cardName, ownerID))

                        cursor.execute("SELECT usdBalance FROM Users WHERE ID = ?", (ownerID,))
                        user = cursor.fetchone()
                        new_balance = user[0]
                    
                        response = f"200 OK\nSOLD: {count} {cardName}. User USD balance ${new_balance:.2f}\n"
                        print(f'Balance updated')
                else:
                    response = '401 Error: invalid balance...\n'
            except ValueError:
                response = '403 Message format error...\n'
            clientSocket.send(response.encode())

#balance function checks if user is logged in and allows the user to check their balance
def balance(clientSocket, msg):
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to check balance\n".encode())
        return
    
    with dbLock:
            try:
                _ = msg
                ownerID = session['userID']
                cursor.execute("SELECT firstName, lastName, usdBalance FROM Users WHERE ID=?", (ownerID,))
                user = cursor.fetchone()
                if user:

                    firstName, lastName, usdBalance = user
                    
                    response = f"200 OK\nBalance for user {firstName} {lastName}: ${usdBalance:.2f}\n"
                    print(f'Balance updated')
                else:
                    response = '401 Error: invalid balance...\n'
            except ValueError:
                response = '403 Message format error...\n'
            clientSocket.send(response.encode())

#Lookup function checks if user is logged in and allows the user to lookup Pokemon Cards
#by their name or type, and checks if no cards are found
def Lookup(clientSocket, msg):
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to lookup cards\n".encode())
        return
    
    with dbLock:
        try:
            # Extract card name after "LOOKUP" command
            _, cardName = msg.split(maxsplit=1)
            ownerID = session['userID']
            
            # Use SQL LIKE for partial matching (case-insensitive with COLLATE NOCASE)
            
            cursor.execute("SELECT * FROM PokemonCards WHERE cardName LIKE ? OR cardType LIKE ? AND ownerID = ? COLLATE NOCASE", 
                           (f"%{cardName}%", f"%{cardName}%", ownerID))
            
            cards = cursor.fetchall()
            cursor.execute("SELECT userName FROM Users WHERE ID = ?",(ownerID,))
            user = cursor.fetchone()

            userName = user[0]

            # Check if there are matched records
            if cards:
                # Construct success response with matched records
                response = "200 OK\nMatch(s) Found:\nID\tCard Name\tType\tRarity\tCount\tOwner_id\n"
                for card in cards:
                    response += f"{card[0]}\t{card[1]}\t{card[2]}\t{card[3]}\t{card[4]}\t{userName}\n"
                print('Match(es) found:', cards)
            else:
                # No matches found
                response = "404 Your search did not match any records\n"
        except ValueError:
            response = "403 Error: Message format error\n"
        except Exception as e:
            response = f"500 Server Error: {str(e)}\n"

    clientSocket.send(response.encode())

#deposit function checks if user is logged in and allows the user to deposit money into their account
def deposit(clientSocket, msg):
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to make deposits\n".encode())
        return
    
    with dbLock:
            try:
                _, amount = msg.split()
                amount = float(amount)
                ownerID = session['userID']

                cursor.execute("SELECT usdBalance FROM Users WHERE ID=?", (ownerID,))

                user = cursor.fetchone()
                
                if user:
                #Gets the balance for respective user and executes transaction
                    user_balance = user[0]
                    total_balance = amount + user_balance

                    cursor.execute("UPDATE Users SET usdbalance=? WHERE ID=?", (total_balance, ownerID))
                    
                    response = f"200 OK\nDEPOSIT: User USD balance ${total_balance:.2f}\n"
                    print(f'Balance updated')
                else:
                    response = '401 Error: invalid amount...\n'
            except ValueError:
                response = '403 Message format error...\n'
            clientSocket.send(response.encode())

#List function checks if user is logged in and root, if root gives full database list
#if user not root, it only lists that users cards
def List(clientSocket):
    session = userSessions.get(clientSocket)
    
    # Check if the user is logged in
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to list cards...\n".encode())
        return

    with dbLock:
        try:
            if session['isRoot']:
                # Root user: get all records
                cursor.execute("SELECT * FROM PokemonCards")
            else:
                # Regular user: get only their records
                ownerID = session['userID']
                cursor.execute("SELECT * FROM PokemonCards WHERE ownerID=?", (ownerID,))
                
            cards = cursor.fetchall()

            
            
            # Prepare the response
            response = "200 OK\n"
            response += "The list of records in the Pokémon cards database:\n" if session['isRoot'] else "The list of records for current user:\n"
            response += "ID\tCard Name\tType\tRarity\tCount\tOwnerID\n"
            
            if cards:
                for card in cards:
                    cursor.execute("SELECT userName FROM Users WHERE ID = ?", (card[5],))
                    user = cursor.fetchone()
                    userName = user[0]
                    response += f"{card[0]}\t{card[1]}\t{card[2]}\t{card[3]}\t{card[4]}\t{userName}\n"
            else:
                response += "No records found.\n"

            clientSocket.send(response.encode())
            print(f'List sent to {clientSocket.getpeername()}')
            
        except Exception as e:
            error_response = f"500 Error: An error occurred while fetching records... {str(e)}\n"
            clientSocket.send(error_response.encode())

#who function checks if user is root and gives a list of active client users
def who(clientSocket, msg):
    # Retrieve the user session for the current client
    session = userSessions.get(clientSocket)
    if not session or not session['loggedIn']:
        clientSocket.send("401 Error: You must be logged in to view active users\n".encode())
        return

    # Only allow root users to use this command
    if not session.get('isRoot'):
        clientSocket.send("403 Forbidden: Only root users can access the WHO command\n".encode())
        return

    # Format the list of active users and their IP addresses
    response = "200 OK\nThe list of active users:\n"
    for userSocket, userInfo in userSessions.items():
        if userInfo['loggedIn']:
            # Extract username and IP address for each logged-in user
            username = userInfo['userName']
            ip_address, _ = userSocket.getpeername()  # Get IP address from the socket
            response += f"{username}\t{ip_address}\n"

    clientSocket.send(response.encode())

#shutdown function checks if user is root and if they are, it allows the user to shutdown
#the server and all open client sockets
def shutdown(clientSocket, serverSocket):

    #get user session data
    session = userSessions[clientSocket]

    if session:
        #get root value from user sessions
            is_root = session.get("isRoot")
            
            
            #if the user is not root user, send error response
            if is_root == 0:
                response = '401 Error: Only root users can shut down the server...\n'
                
                print(response+'\n')
                clientSocket.send(response.encode())
                return
            elif is_root == 1:
                #if the user is the root user, shut down all client sockets, server socket, remove user sessions and shutdown server
                print("Shutting down server...")
                for clientSocket in list(userSessions.keys()):
                    clientSocket.send('200 OK: Server is shutting down. Goodbye...'.encode())
                    clientSocket.close()
                    if clientSocket in sockets_list:
                        sockets_list.remove(clientSocket)
                    del userSessions[clientSocket]
                serverSocket.close()
                sys.exit(0)
            else:
                #in case conditional evaluates an error/none for root value
                response = '401 Error: Only root user can shut down the server...\n'
                clientSocket.send(response.encode())
                return
    else:
            #in case conditional evaluates an error/none for root value
            response = '401 Error: Only root user can shut down the server...\n'
            clientSocket.send(response.encode())
            return

#Quit function allows any user to shut down their respective client and close the socket/client
#connection
def quit(clientSocket):
    # Attempt to send farewell message
    response = '200 OK: Farewell.\n'
    try:
        if clientSocket in socketList:
            clientSocket.send(response.encode())
    except OSError as e:
        # Handle the case where the socket is already closed
        print(f'Failed to send farewell to {clientSocket.getpeername()}: {str(e)}')

    # Clean up user session and disconnect client
    disconnect(clientSocket)

    
if __name__ == '__main__':
    #establish database connection
    dbConnection = sqlite3.connect('pokemonTrade.db', check_same_thread=False)
    cursor = dbConnection.cursor()
    #insert default database entries if they do not already exist
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
                       ('root@pokemontrade.com', 'Root', 'User', 'root', 'root01', 100.0, 1))
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('john@example.com', 'John', 'Doe', 'john', 'john01', 50.0, 0))
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('mary@example.com', 'Mary', 'Smith', 'mary', 'mary01', 75.0, 0))
        cursor.execute("INSERT INTO Users (email, firstName, lastName, userName, password, usdBalance, isRoot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('moe@example.com', 'Moe', 'Smart', 'moe', 'moe01', 25.0, 0))
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