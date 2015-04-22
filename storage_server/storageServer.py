import socket
import threading
import os
import select
import fileManage
import shutil
import time
from parsePath import parsePath
from parsePath import checkExist
from parsePath import checkDir

#MT_status = 0
#RR_status = 0
timeout = 0.5 #1 second
#index = 0
nodeID = -1

class log:
    def __init__(self, filename):
        self.filename = filename

    def append(self, message):
        with open(self.filename,'a') as f:
            f.write(message+'\n')
    
    def read_line(self, line):
        if line > self.get_latest_index():
            print('no such line.')
            return ''
        log = ''
        with open(self.filename) as f:
           log = f.readlines()[line-1]
        log = log.strip('\n')
        return log
        
    def get_latest_index(self):
        with open(self.filename) as f:
            lines = len(f.readlines())
        return lines
    
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

    def initLog(self):
        lines = self.get_latest_index()
        if lines != 0:
            lastLine = self.read_line(lines)
            words = lastLine.split(" ")
            if words[-1] == 'uncommitted':
                self.delete_last_line()        





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
def parseLogPath(Path):
    logPath = []
    if len(Path) == 7:
        logPath = '.'
    else:
        logPath = Path[8:]
    return logPath


def rollBack(lastLog):
    words = lastLog.split(' ')
    if words[-1] == 'committed':
        return 'Last log was committed'
    elif words[-1] == 'uncommitted':
        if words[1] == 'upload':
            path = words[2]
            path = ('node%s/' % nodeID) + path
            filename = words[3]
            fileManage.RBupload(path, filename)
        elif words[1] == 'rm':
            path = ('node%s/' % nodeID) + words[2]
            fileManage.RBrm(path)
        elif words[1] == 'mkdir':
            path = words[2]
            path = ('node%s/' % nodeID) + path
            dirName = words[3]
            fileManage.RBmkdir(path, dirName)
        elif words[1] == 'rmdir':
            path = ('node%s/' % nodeID) + words[2]
            fileManage.RBrm(path)

        return 'Last log was uncommitted. Last operation has been rolled back.'
    else:
        return 'Last log has no commit/uncommit info.'

def removeTmp(args, dirname, filenames):
    currPath = os.path.abspath(dirname)
    splitDir =[(filename, filename.split('##')) for filename in filenames]
    fileToRemove = filter(lambda x: os.path.exists(os.path.join(currPath, x[0])) and len(x[1]) == 3 and x[1][2] == '$', splitDir)    
    for filename in fileToRemove:
        toDelete = os.path.join(currPath, filename[0])
        if os.path.isdir(toDelete):
            shutil.rmtree(toDelete)
        else:
            os.remove(toDelete)
        print os.path.join(toDelete)

def garbageCollection():
    path = ('node%s' % nodeID)    
    os.path.walk(path, removeTmp, None)
    
def handler(name, sock, section):
    # sock.setblocking(0)
    sock.send(str(nodeID))
#    index = 0
    mylog = log(('node%s.log' % nodeID))#TODO create node1.log first in Main()
    if(mylog.get_latest_index() != 0):
        print rollBack(mylog.read_line(mylog.get_latest_index()))
        mylog.initLog()
    while True:
        ready = select.select([sock], [], [], timeout)
        if ready[0]:
            print 'request received(%s)' % section
            request = sock.recv(1024)
            words = request.split(" ")
            command = words[0]
            if command == 'cd' and section == 'R':
                path = []
                if len(words) == 1:
                    path = ('node%s/' % nodeID)
                else:
                    path = ('node%s/' % nodeID) + words[1]
                rPath = parsePath(path, section)
                if rPath != 'Path invalid':
                    fileManage.rtnFile(rPath, sock)
                else:
                    sock.send('Path invalid')

            elif command == 'ls':
                sock.send('Receive ls')                
            elif command == 'upload':
                path = words[1]
                path = ('node%s/' % nodeID) + path
                rPath = parsePath(path, section)
                filename = words[2]
                size = long(words[3])
                if checkExist(rPath, filename):
                    sock.send('File already exists')#overwrite the existing file or not
                    continue
                if rPath != 'Path invalid':#TODO, parse to local
                    rFilename = filename
                    if section == 'R':
                        rFilename = filename + '##' + str(mylog.get_latest_index() + 1)
                    logPath = parseLogPath(rPath)
                    mylog.append((str(mylog.get_latest_index() + 1) + ' upload ' + logPath + ' ' + rFilename + ' ' + words[3] + ' uncommitted'))
                    status = fileManage.uploadFile(rPath, rFilename, sock, size)
                    if status == 'success':
                        print 'upload success'
                        mylog.modify_last_line((str(mylog.get_latest_index()) + ' upload ' + logPath + ' ' + rFilename + ' ' + words[3] + ' committed'))
                        if section == 'R':
                            sock.send(mylog.read_line(mylog.get_latest_index()))
                    #TODO: commit log
                    elif status == 'fail':
                        mylog.delete_last_line()
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
                path = words[1]
                path = ('node%s/' % nodeID) + path
                filename = words[2]
                rPath = parsePath(os.path.join(path,filename), section)
                if rPath != 'Path invalid':
                    if os.path.isdir(rPath):
                        sock.send('Not file')
                        continue
                    logPath = parseLogPath(parsePath(path, section))
                    rFilename = filename
                    if section == 'R':
                        rFilename = rPath.split('/')[-1]
                    mylog.append(str(mylog.get_latest_index() + 1) + ' rm ' + logPath + ' ' + rFilename + ' uncommitted')
                    status = fileManage.removeFile(rPath, sock)
                    if status == 'success':
                        print 'rm success'
                        mylog.modify_last_line(str(mylog.get_latest_index()) + ' rm ' + logPath + ' ' + rFilename + ' committed')
                        if section == 'R':
                            sock.send(mylog.read_line(mylog.get_latest_index()))
                    elif status == 'fail':
                        mylog.delete_last_line()
                else:
                    sock.send('File not exists')
 
            elif command == 'mkdir':
                path = words[1]
                path = ('node%s/' % nodeID) + path
                rPath = parsePath(path, section)
                dirName = words[2]
                if checkExist(rPath, dirName):
                    sock.send('Directory already exists')
                    continue
                if rPath != 'Path invalid':
                    rdirName = dirName
                    if section == 'R':
                        rdirName = dirName + '##' + str(mylog.get_latest_index() + 1)
                    logPath = parseLogPath(rPath)
                    mylog.append((str(mylog.get_latest_index() + 1) + ' mkdir ' + logPath + ' ' + rdirName + ' uncommitted'))
                    status = fileManage.mkdir(rPath, rdirName, sock)
                    if status == 'success':
                        print 'mkdir success'
                        mylog.modify_last_line((str(mylog.get_latest_index()) + ' mkdir ' + logPath + ' ' + rdirName + ' committed'))
                        if section == 'R':
                            sock.send(mylog.read_line(mylog.get_latest_index()))
                    #TODO: commit log
                    elif status == 'fail':
                        mylog.delete_last_line()
                else:
                    sock.send('Path invalid')


            elif command == 'rmdir':
                path = words[1]
                path = ('node%s/' % nodeID) + path
                rPath = parsePath(path, section)
                if rPath != 'Path invalid':
                    if checkDir(rPath):
                        sock.send('Directory is not empty')
                        continue
                    if os.path.isfile(rPath):
                        sock.send('Not directory')
                        continue
                    logPath = parseLogPath(rPath)
                    mylog.append((str(mylog.get_latest_index() + 1) + ' rmdir ' + logPath + ' uncommitted'))
                    status = fileManage.rmdir(rPath, sock)
                    if status == 'success':
                        print 'rm success'
                        mylog.modify_last_line((str(mylog.get_latest_index()) + ' rmdir ' + logPath + ' committed'))
                        if section == 'R':
                            sock.send(mylog.read_line(mylog.get_latest_index()))
                    elif status == 'fail':
                        mylog.delete_last_line()
                else:
                    sock.send('Directory not exists')

            elif command == 'index':
                sock.send(str(mylog.get_latest_index()))
            elif command == 'log':
                sock.send(mylog.read_line(mylog.get_latest_index()))
            elif command == 'heartBeat':
                sock.send('alive')
            elif command == 'garbage':
                garbageCollection()
                sock.send('garbage collected')
                #TODO: reply or not
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
    global MT_status
    MT_status = 0
    global RR_status
    RR_status = 0
    nodeID = int(raw_input("node ID: -> "))
    #init storage directory and log
    path = ('node%s/' % nodeID)
    if os.path.exists(path) == False:
        os.mkdir(path)
    logName = 'node' + str(nodeID) + '.log'
    if os.path.isfile(logName) == False:
        fp = open(logName, 'w')
        fp.close()
    while True:
        command = raw_input("Command: (type:\"on\" to connect; \"off\" to block) -> ")
        if command == 'on' and MT_status == 0 and RR_status == 0:
            #connect to maintain
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.connect((host, port_MT))
            MT_status = 1
            print "Master Server Connected (Maintain)."
            t1 = threading.Thread(target = Maintain, args = ("MT", s1))
            t1.setDaemon(True)
            t1.start()
            #connect to ResponseRequest
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((host, port_RR))
            RR_status = 1
            print "Master Server Connected (ResponseRequest)."
            t2 = threading.Thread(target = ResponseRequest, args = ("RR", s2))
            t2.setDaemon(True)
            t2.start()

        elif command == 'off' and MT_status == 1 and RR_status == 1:
            MT_status = 0
            RR_status = 0
            print "Master Server Disconnected (Maintain)."
            print "Master Server Disconnected (ResponseRequest)."

        time.sleep(2*timeout)


if __name__ == '__main__':
    Main()
