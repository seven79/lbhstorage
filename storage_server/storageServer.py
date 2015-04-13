import socket
import threading
import os
import select
import fileManage


MT_status = 0
RR_status = 0
timeout = 1 #1 second

def handler(name, sock, section):
    sock.setblocking(0)
    index = 0
    while True:
        ready = select.select([sock], [], [], timeout)
        if ready[0]:
            print 'request received(%s)' % section
            request = sock.recv(1024)
            words = request.split(" ")
            command = words[0]
            if command == 'cd':
                path = words[1]
                fileManage.rtnFile(path, sock)
            elif command == 'ls':
                sock.send('Receive ls')                
            elif command == 'upload':
                path = words[1]
                filename = words[2]
                size = long(words[3])
                if os.path.isdir(path):#TODO, parse to local
                    fileManage.uploadFile(path, filename, sock, size)
                    index += 1
                else:
                    sock.send('Path invalid')
            elif command == 'download':
                print 'download'
            elif command == 'rm':
                index += 1
            elif command == 'mkdir':
                index += 1
            elif command == 'rmdir':
                index += 1
            elif command == 'cp':
                index += 1

        else:
            print 'wait for message(%s)' % section
            if section == 'R' and RR_status == 0:
                print 'close socket (%s)' % section
                sock.close()
                break
            elif section == 'M' and MT_status == 0:
                print 'close socket (%s)' % section
                sock.close()
                break


def ResponseRequest(name, sock):
    handler(name, sock, 'R')

def Maintain(name, sock):
    handler(name, sock, 'M')

def Main():
    #connect to Master Server
    host = raw_input("Master Host: -> ")
    port_MT = int(raw_input("Master Port (MT): -> "))
    port_RR = int(raw_input("Master Port (RR): -> "))


    while True:
        command = raw_input("Command: (type:\"on\" to connect; \"off\" to block) -> ")        
        if command == 'on' and MT_status == 0 and RR_status == 0:
            #connect to maintain
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.connect((host, port_MT))
            global MT_status
            MT_status = 1
            print "Master Server Connected (Maintain)."
            t1 = threading.Thread(target = Maintain, args = ("MT", s1))
            t1.start()
            #connect to ResponseRequest
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((host, port_RR))
            global RR_status
            RR_status = 1
            print "Master Server Connected (ResponseRequest)."
            t2 = threading.Thread(target = ResponseRequest, args = ("RR", s2))
            t2.start()

        elif command == 'off' and MT_status == 1 and RR_status == 1:
            global MT_status
            MT_status = 0
            global RR_status
            RR_status = 0
            print "Master Server Disconnected (Maintain)."
            print "Master Server Disconnected (ResponseRequest)."


if __name__ == '__main__':
    Main()
