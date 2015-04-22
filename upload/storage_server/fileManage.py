import os.path
import socket

def rtnFile(path, sock):
    listName = os.listdir(path)
    sendBuffer = ''
    for filename in listName:
        filepath = os.path.join(path, filename)
        tmp = filename.split('##')
        sFilename = tmp[0]
        if sFilename != '.' and len(tmp) <= 2:
            if os.path.isdir(filepath):
                sendBuffer += ('/' + sFilename + '\n')
            elif os:
                sendBuffer += (sFilename + '\n')
    if sendBuffer == '':
        sock.send('(No file in this directory)')
    else:
        sock.send(sendBuffer)
    
def uploadFile(path, filename, sock, size):
    #print 'path:' + path
    #print 'filename:'+ filename
    sock.send('OK')
    f = open(os.path.join(path ,filename), 'wb')
    data = sock.recv(1024)
    totalRecv = len(data)
    f.write(data)
    while totalRecv < size:
        data = sock.recv(1024)
        totalRecv += len(data)
        f.write(data)
        #print "{0:.2f}".format((totalRecv/float(size))*100) + "% Done"
    f.close()
    #print "Upload Complete!"
    sock.send("commit")
    rev = sock.recv(1024)
    if rev == 'ACK':
        return 'success'
    elif rev == 'Fail':
        os.remove(os.path.join(path ,filename))
        return 'fail'

def downloadFile(path_filename, sock):
    sock.send('EXISTS ' + str(os.path.getsize(path_filename)))
    #print 'EXISTS ' + str(os.path.getsize(path_filename))
    with open(path_filename, 'rb') as f:
        bytesToSend = f.read(1024)
        sock.send(bytesToSend)
        while bytesToSend != "":
            bytesToSend = f.read(1024)
            sock.send(bytesToSend)

            
def removeFile(filename, sock):
    os.rename(filename, (filename + '##$'))
    #print "rm Complete!"
    sock.send("commit")
    rev = sock.recv(1024)
    if rev == 'ACK':
        return 'success'
    elif rev == 'Fail':
        os.rename((filename + '##$'), filename)
        return 'fail'

def mkdir(path, dirName, sock):
    os.mkdir(os.path.join(path, dirName))
    #print "mkdir Complete!"
    sock.send("commit")
    rev = sock.recv(1024)
    if rev == 'ACK':
        return 'success'
    elif rev == 'Fail':
        os.remove(os.path.join(path ,dirName))
        return 'fail'




def rmdir(dirName, sock):
    os.rename(dirName, (dirName + '##$'))
    #print "rmdir Complete!"
    sock.send("commit")
    rev = sock.recv(1024)
    if rev == 'ACK':
        return 'success'
    elif rev == 'Fail':
        os.rename((dirName + '##$'), dirName)
        return 'fail'
    
def RBupload(path, filename):
    filepath = os.path.join(path, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        #print '%s removed' % filepath
    #else:
        #print '%s file not exsits' % filepath

def RBrm(path):
    pathStored = path + '##$'
    if os.path.exists(pathStored):
        os.rename(pathStored, path)
        #print '%s recovered' % path
    #else:
        #print '%s file not exsits' % pathStored

def RBmkdir(path, filename):
    filepath = os.path.join(path, filename)
    if os.path.exists(filepath):
        os.rmdir(filepath)
        #print '%s removed' % filepath
    #else:
        #print '%s directory not exsits' % filepath



    
    
    
