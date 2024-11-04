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

        1. BUY <CardName> <CardType> <Rarity> <Price> <Quantity>
        2. SELL <CardName> <Quantity> <Price>
        3. LIST
        4. BALANCE
        5. DEPOSIT <amount>
        6. LOOKUP <CardName> OR <CardType>
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

        1. LOGIN <Username> <Password>
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
        #process login command
        if'200 OK' in msg and 'Logged in' in msg:
            self.loggedIn = True
            fullMenu()
        elif'200 OK' in msg and 'Logged out user' in msg:
            self.loggedIn = False   #process logging out.
            preLoginMenu()
        elif 'shutting down' in msg.lower():
            print("Server is shutting down. Exiting client...")
            self.closeConnection() #process shutting down the server if response is valid
            sys.exit(0)
        elif'200 OK' in msg and 'Farewell' in msg:
            print('Quitting Pokemon trading app...\n')          #if client chooses to commit close socket and connection to server

            self.closeConnection()
            sys.exit(0)
        elif '401 Error' in msg: #if response results in error print the response
            print(msg + '\n')
            if not self.loggedIn:
                preLoginMenu()
            else:
                fullMenu()
        else:
            if not self.loggedIn:   
                preLoginMenu()
            else:
                fullMenu()


    def closeConnection(self):
        if self.s:
            print("Closing connection...")
            self.s.close()  # Close the socket
            self.s = None 

    def send(self, command):
        try:
            self.s.send(f"{command}\n".encode())
            self.onread()  # Process server response
        except (BrokenPipeError, ConnectionResetError) as e:
            print("Server closed the connection. Unable to send message.")
            self.closeConnection()  # Ensure the client socket is closed
            sys.exit(1)


class Input():

    def __init__(self, sender):
        self.sender = sender
    def fileno(self):
        return sys.stdin.fileno()

    def onread(self):
        sys.stdout.write("Enter command: ")
        sys.stdout.flush()

        msg = sys.stdin.readline().strip()  # Read input from stdin
        if msg:  # Ensure we are sending a non-empty message
            self.sender.send(msg)  # Send the command to the server
            if msg.upper() == "QUIT":  # If QUIT command is detected
                self.sender.closeConnection()  # Close the connection
                print("Exiting client...")
                sys.exit(0)

class EventLoop():

    def __init__(self):
        self.readers = []

    def addReader(self, reader):
        self.readers.append(reader)


    def removeReader(self, reader):
        if reader in self.readers:
            self.readers.remove(reader)

    def runForever(self):
        #loop for checking all readable sockets, and if they are ready to read, execute onread to process command/receive data/send response
        while True:
            try:
                readers, _, _ = select.select(self.readers, [], [])

                for reader in readers:
                    if reader.fileno() < 0:  # Check if the file descriptor is valid
                        continue
                    reader.onread()
            except Exception as e:
                print(f"Error in event loop: {str(e)}")
                break

    #initialize connection to server and add socket to event loop list/ this loop will monitor for input/response simultaneously
def processClient( serverHost, serverPort):
    connection = Connection(serverHost, serverPort)  # Create a connection instance
    input_handler = Input(connection)  # Create an input handler for sending commands

    event_loop = EventLoop()  # Create the event loop
    event_loop.addReader(connection)  # Add the connection to the event loop
    event_loop.addReader(input_handler)  # Add the input handler to the event loop

    try:
        preLoginMenu()
        event_loop.runForever()  # Start the event loop
    except Exception as e:
        print(f"Error in processing client: {e}")
    finally:
        connection.closeConnection() 
    
if __name__ == '__main__':
    main()

