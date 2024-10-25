# from multiprocessing import Event
import socket
import sys
import select
import threading
BUFFER_SIZE = 4096

def fullMenu():

    print('''
    ----- POKEMON TRADING APP -----
    
    --- commands and parameters ---

        1. BUY
        2. SELL
        3. LIST
        4. BALANCE
        5. DEPOSIT
        6. LOOKUP
        7. WHO (root only)
        8. LOGOUT
        9. QUIT
       10. SHUTDOWN

       ''')
    sys.stdout.write("Enter command: ")
    sys.stdout.flush()





def preLoginMenu():

    print('''
    ----- POKEMON TRADING APP -----
    
    --- commands and parameters ---

        1. LOGIN
        2. QUIT

       ''')
    sys.stdout.write("Enter command: ")
    sys.stdout.flush()


def main():

    if len(sys.argv) != 3:
        print("Error: please start server by running python3 Client.py <serverIP> <serverPort>")
        sys.exit(1)
    
    serverHost = sys.argv[1]
    try:
        serverPort = int(sys.argv[2])
    except ValueError:
        print("Error: serverPort must be an integer.")
        sys.exit(1)
    
  


    #clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #clientSocket = connectToServer(serverHost, serverPort)

   

    #preLoginMenu(clientSocket)
    processClient( serverHost, serverPort)





class Connection():
    def __init__(self, serverHost, serverPort):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((serverHost, serverPort))
        self.loggedIn = False
        

    def fileno(self):
        return self.s.fileno()

    def onread(self):
        msg = self.s.recv(BUFFER_SIZE).decode()
        print(msg)

        if'200 OK' in msg and 'Logged in successfully' in msg:
            self.loggedIn = True
            fullMenu()
        else:

            if not self.loggedIn:
                preLoginMenu()
            else:
                fullMenu()


    def send(self, msg):
        self.s.send(msg)


class Input():

    def __init__(self, sender):
        self.sender = sender
    def fileno(self):
        return sys.stdin.fileno()

    def onread(self):
        sys.stdout.write("Enter command: ")
        sys.stdout.flush()

        msg = sys.stdin.readline()
        self.sender.send(msg.encode())


class EventLoop():

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
        
def processClient( serverHost, serverPort):

    connection = Connection(serverHost, serverPort)
    #insert this somewhere else later
    preLoginMenu()
    inputReader = Input(connection)
    eventLoop = EventLoop()
    eventLoop.addReader(connection)
    eventLoop.addReader(inputReader)
    eventLoop.runForever()
    
          
    

           



if __name__ == '__main__':
    main()


# def connectToServer(serverHost, serverPort):
    
#     try:
#         clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         clientSocket.connect((serverHost, serverPort))
        
#         print(f"Connection to {serverHost}:{serverPort}\nhas been established")

#         return clientSocket
#     except Exception as e:

#         print(f"failed to connect to server: {e}")
#         sys.exit(1)





# isLoggedOn = False

# def preLoginMenu(clientSocket):
    
   


#     while isLoggedOn ==False:

#         print('\n--Pre-Login Menu--\n')
#         print("1. LOGIN\n")
#         print("2. QUIT\n")
        
#         input_thread = threading.Thread(target=processUserInput, args=(clientSocket, isLoggedOn))
#         input_thread.daemon = True  # Daemon thread will automatically exit when the main program exits
#         input_thread.start()
#         socketList = [clientSocket]

#         readableSockets, _, _ = select.select(socketList, [], [])
     


#         for sock in readableSockets:

#             if sock == clientSocket:

#                 message = clientSocket.recv(BUFFER_SIZE).decode()
                
#                 if not message:
                    
#                     print('disconnected from the server...\n')
#                     sys.exit(0)
#                 else:

#                     print(f'{message}')

       

#     fullMenu(clientSocket)

        
# def processUserInput(clientSocket, loggedIn):

#     while True:
#         selection = input('Please enter a command: ')
#         message = sys.stdin.readline
#         if selection == '1' or '2' or '3' or '4' or '5' or '6' or '7' or '8' or '9' or '10' or '11':
#             processCommand(clientSocket, selection, loggedIn)
        
            




# def fullMenu(clientSocket):



#     while True:
#         print('''------POKEMON TRADING APP------
            
#                 1.BUY
#                 2.QUIT
#                 3.LIST
#                 4.BALANCE
#                 5.DEPOSIT
#                 6.LOOKUP
#                 7.WHO(root only)
#                 8.LOGOUT
#                 9.SELL
#             10.SHUTDOWN
#                             ''')
        
#         socketList = [clientSocket]

#         readableSockets, _, _ = select.select(socketList, [], [])
     


#         for sock in readableSockets:

#             if sock == clientSocket:

#                 message = clientSocket.recv(BUFFER_SIZE).decode()
                
#                 if not message:
                    
#                     print('disconnected from the server...\n')
#                     sys.exit(0)
#                 else:

#                     print(f'{message}')
       
       

        


# def processCommand(clientSocket, message, loggedIn):
#         selection = message
#         print('entering command seq')
#         print(f'is logged on: {loggedIn} {isLoggedOn}')
#         if isLoggedOn == True or loggedIn == True:
#             if selection == '1':
#                 sendBUY(clientSocket)
#             elif selection == '2':
#                 sendSELL(clientSocket)
#             elif selection == '3':
#                 sendLIST(clientSocket)
#             elif selection == '4':
#                 sendBALANCE(clientSocket)
#             elif selection == '5':
#                 #sendDEPOSIT(clientSocket)
#                 x=10
#             elif selection == '6':
#                 #sendLOOKUP(clientSocket)
#                 x=10
#             elif selection == '7':
#                 #sendWHO(clientSocket)
#                 x=10
#             elif selection == '8':
#                 #sendLOGOUT(clientSocket)
#                 x=10
#             elif selection == '9':
#                 sendQUIT(clientSocket)   
#             elif selection == '10':
#                 sendSHUTDOWN(clientSocket)
#             else:
#                 print('invalid command please try again...\n')
#         else:
#             print(selection)
#             if selection == '1':
#                 loggedIn = login(clientSocket)
               
#             elif selection == '2':
#                 sendQUIT(clientSocket)
#             else:
#                 print('invalid command please try again...\n')


# def sendSHUTDOWN(clientSocket):
#     print("--SHUTDOWN MENU--\n")
#     confirm = input("Are you sure you want to shut down the server? Enter y to confirm or n to cancel: ")
    
#     if confirm == 'y':
#         command = "SHUTDOWN\n"
#         clientSocket.send(command.encode())

#         response = clientSocket.recv(BUFFER_SIZE).decode()
#         print(response)

# def sendBALANCE(clientSocket):
#     print("--BALANCE MENU--\n")
#     ownerID = input("Enter your User ID: ")
        
#     command = f"BALANCE {ownerID}\n"
#     clientSocket.send(command.encode())

#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)

# def sendQUIT(clientSocket):
    
#     command = "QUIT\n"

#     clientSocket.send(command.encode())

#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)
#     sys.exit(0)

# def sendLIST(clientSocket):
#     print("--LIST MENU--\n")
#     ownerID = input("Enter your User ID: ")
        
#     command = f"LIST {ownerID}\n"
#     clientSocket.send(command.encode())

#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)

# def sendSELL(clientSocket):
#     print("--SELL MENU--\n")
#     ownerID = input("Enter your User ID: ")
#     cardName = input("Enter card name: ")
#     quantity = input("Enter sell quantity: ")
#     price = input("Enter price of card: ")
        

#     command = f"SELL {ownerID} {cardName} {quantity} {price}\n"
#     clientSocket.send(command.encode())

#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)


# def sendBUY(clientSocket):
#     print("--BUY MENU--\n")
#     ownerID = input("Enter your User ID: ")
#     cardName = input("Enter card name: ")
#     rarity = input("Enter card rarity: ")
#     cardType = input("Enter card type: ")
#     price = input("Enter price of card: ")
#     count = input("Enter # of card/s to buy: ")



#     try:
#             #cast parameter to strictly integer to avoid errors in sqlite query
#            count = int(count)
#     except ValueError:
#             return f"Error: invalid count amount was entered."

#     #do not send response to server until valid buy amount is entered
#     if( count < 1 ):

#         while(count < 1):
            
#             #if client decides that they would like to cancel command or entered in wrong command on accident
#             count = input("Enter in a card amount greater than 0 or enter x to cancel buy command: ")
#             if(count == 'x'):
#                 return
        
        

#     command = f"BUY {ownerID} {cardName} {rarity} {cardType} {price} {count}\n"
#     clientSocket.send(command.encode())

#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)



# def login(clientSocket):
#     global isLoggedOn
#     username = input('Enter username: ')
#     password = input('Enter password: ')
#     message = f'LOGIN {username} {password}'
#     print(f'sending: {message}\n')
#     clientSocket.send(message.encode())




#     response = clientSocket.recv(BUFFER_SIZE).decode()
#     print(response)

#     if '200 OK' in response:
#         isLoggedOn = True
#         return True
#     else:
#         print(response)


