import socket
import threading
import os
import select
import fileManage
from parsePath import parsePath

MT_status = 0
RR_status = 0
timeout = 1 #1 second
index = 0
nodeID = -1



class log:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename) as f:
            self.filelines = len(f.readlines())

    def append(self, message):
        with open(self.filename,'a') as f:
            f.write(message+'\n')
    
    def read_line(self, line):
        if line > filelines:
            print('no such line.')
            return ''
        log = ''
        with open(self.filename) as f:
           log = f.readlines()[line-1]
        log = log.strip('\n')
        return log
        
    def get_latest_index(self):
        with open(self.filename) as f:
            self.filelines = len(f.readlines())
        return self.filelines
    
    def delete_last_line(self):
        curr = []
        with open(self.filename) as f:
            lines = f.readlines()
            curr = lines[:-1]
        with open(self.filename,'w') as f:
            f.writelines(curr)
    
    def modify_last_line(self, message):
        self.delete_last_line()
        self.append(message)





'''def parsePath(path, section):
   ''''''note: 
    mkdir generate: path##id
    rmdir generate: path##id##tmp
    upload generate: filename##id
    rm generate: filename##id##tmp
    mv generate: filename##id##tmp filename##newid##tmp
    cp generate: filename##newid
   ''''''
    if section == 'R':
        currPath = '.'
        dirs = path.split('/')
        for directory in dirs:
            splitDir =[(filename, filename.split('##')) for filename in os.listdir(currPath)]

            currPath += ('/' + filter(lambda x: os.path.isdir(x[0]) and len(x[1]) == 2 and x[1][0] == directory, splitDir))
        return currPath
            
'''
def handler(name, sock, section):
    # sock.setblocking(0)
    sock.send(str(nodeID))
    index = 0
    mylog = log(('node%s.log' % nodeID))#TODO create node1.log first in Main()
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
                path = ('node%s/' % nodeID) + path
                rPath = parsePath(path, section)
                filename = words[2]
                size = long(words[3])
                if rPath != 'Path invalid':#TODO, parse to local
                    rFilename = filename + '##' + str(mylog.get_latest_index())
                    mylog.append((str(mylog.get_latest_index() + 1) + ' upload ' + rPath + ' ' + rFilename + ' ' + words[3] + ' uncommitted'))
                    status = fileManage.uploadFile(rPath, rFilename, sock, size)
                    if status == 'success':
                        print 'upload success'
                        mylog.modify_last_line((str(mylog.get_latest_index()) + ' upload ' + rPath + ' ' + rFilename + ' ' + words[3] + ' committed'))
                    #TODO: commit log
                    elif status == 'fail':
                        mylog.delete_last_line()
                        continue
                    #index += 1
                else:
                    sock.send('Path invalid')
            elif command == 'download':
                path = words[1]
                path = ('node%s/' % nodeID) + path
                filename = words[2]
                rPath = parsePath(os.path.join(path,filename), section)
                if rPath != 'Path invalid':#TODO, parse to local
                    fileManage.downloadFile(rPath, sock)
                else:
                    sock.send('File not exists')
            elif command == 'rm':
                oper = words[3]
                path = words[1]
                filename = words[2]
                if os.path.exists(os.path.join(path,filename)):
                    if oper == 'P':
                        fileManage.removeFile(path, filename, sock)
                        mylog.append((str(mylog.get_latest_index() + 1) + ' ' + request))
                        #index += 1
                    elif oper == 'T':
                        fileManage.toTmpFile(path, filename, sock, str(mylog.get_latest_index() + 1))
                        mylog.append((str(mylog.get_latest_index() + 1) + ' ' + request))
                else:
                    sock.send('File not exists')
            elif command == 'rmtmp':
                path = words[1]
                filename = words[2]
                opIndex = words[3]
                tmpFile = filename + '##' + str(opIndex + 1) + '##tmp'
                if os.path.exists(os.path.join(path, tmpFile)):
                    fileManage.removeFile(path, tmpFile, sock)
                    #index += 1
                else:
                    sock.send('File not exists')
            elif command == 'mkdir':
                path = words[1]
                dirName = words[2]
                if os.path.exists(path) and os.path.exists(os.path.join(path, filename)) == False:
                    fileManage.mkdir(path, dirName, sock)
                    mylog.append((str(mylog.get_latest_index() + 1) + ' ' + request))
                elif os.path.exists(os.path.join(path, filename)):
                    sock.send('dir already exists')
                else:
                    sock.send('path error')
            elif command == 'rmdir':
                path = words[1]
                dirName = words[2]
                if os.path.exists(path) and os.path.exists(os.path.join(path, filename)) == False:
                    fileManage.mkdir(path, dirName, sock)
                    mylog.append((str(mylog.get_latest_index() + 1) + ' ' + request))
                elif os.path.exists(os.path.join(path, filename)):
                    sock.send('dir already exists')
                else:
                    sock.send('path error')
                    index += 1
            elif command == 'mv':
                index += 1
            elif command == 'cp':
                index += 1
            elif command == 'index':
                sock.send(str(mylog.get_latest_index()))

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
    default_option = raw_input("use default (127.0.0.1 8000 8001):(y/n) -> ")
    host = ''
    port_MT = 0
    port_RR = 0
    if default_option == 'n':
        host = raw_input("Master Host: -> ")
        port_MT = int(raw_input("Master Port (MT): -> "))
        port_RR = int(raw_input("Master Port (RR): -> "))
    elif default_option == 'y':
        host = '127.0.0.1'
        port_MT = 8001
        port_RR = 8000
    else:
        print 'wrong choice'
        exit()
    print "host: " + host + " MT:" + str(port_MT) + " RR:" + str(port_RR)
    global nodeID
    nodeID = int(raw_input("node ID: -> "))
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
            t1.setDaemon(True)
            t1.start()
            #connect to ResponseRequest
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((host, port_RR))
            global RR_status
            RR_status = 1
            print "Master Server Connected (ResponseRequest)."
            t2 = threading.Thread(target = ResponseRequest, args = ("RR", s2))
            t2.setDaemon(True)
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
