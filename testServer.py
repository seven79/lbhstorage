import socket
import threading
import os

def userRequest(name, sock):
    while True:
        userInput = raw_input("storage connected:\n Request: -> ")
        words = userInput.split(" ") 
        if words[0] == 'upload':
            path = words[1]
            filename = words[2] 
            userInput += (' ' + str(os.path.getsize(filename)))
            print userInput
            sock.send(userInput)
            res = sock.recv(1024)
            if res == 'Path invalid':
                print 'Path invalid'
            elif res == 'OK':
                print 'OK'
                with open(filename, 'rb') as f:
                    print '%s opened' % filename
                    bytesToSend = f.read(1024)
                    sock.send(bytesToSend)
                    while bytesToSend != "":
                        bytesToSend = f.read(1024)
                        sock.send(bytesToSend)
        elif words[0] == 'download':
            filename = words[2] 
            sock.send(userInput)
            res = sock.recv(1024)
            ans = res.split(" ")
            if ans[0] == 'EXISTS':
                print 'file exists'
                size = long(ans[1])
                f = open(filename, 'wb')
                data = sock.recv(1024)
                totalRecv = len(data)
                f.write(data)
                while totalRecv < size:
                    print str(totalRecv) + '/' + str(size)
                    data = sock.recv(1024)
                    totalRecv += len(data)
                    f.write(data)
                    print "{0:.2f}".format((totalRecv/float(size))*100) + "% Done"
                f.close()
                print "Download Complete!"
            else:
                print 'No such file'
                        
        else:
            sock.send(userInput)
            userResponse = sock.recv(1024)
            print userResponse
    sock.close()

def Main():
    host = '127.0.0.1'
    port = int(raw_input("PORT: -> "))

    s = socket.socket()
    s.bind((host, port))
    s.listen(5)

    print "Server Started."
    while True:
        c, addr = s.accept()
        print "client connected ip: <" + str(addr) + ">"
        t = threading.Thread(target = userRequest, args = ("userRequest", c))
        t.start()

    s.close()

if __name__ == '__main__':
    Main()
