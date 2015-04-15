import os.path
import socket

def rtnFile(path, sock):
    list = os.listdir(path)
    buffer = ''
    for file in list:
        filepath = os.path.join(path, file)
        if file[0] != '.':
            if os.path.isdir(filepath):
                buffer += ('/' + file + '\n')
            elif os:
                buffer += (file + '\n')
    sock.send(buffer)

def uploadFile(path, filename, sock, size):
    print 'path:' + path
    print 'filename:'+ filename
    sock.send('OK')
    f = open(os.path.join(path ,filename), 'wb')
    data = sock.recv(1024)
    totalRecv = len(data)
    f.write(data)
    while totalRecv < size:
        data = sock.recv(1024)
        totalRecv += len(data)
        f.write(data)
        print "{0:.2f}".format((totalRecv/float(size))*100) + "% Done"
    f.close()
    print "Upload Complete!"
    sock.send("commit")
    rev = sock.recv(1024)
    if rev == 'ACK':
        return 'success'
    elif rev == 'Fail':
        os.remove(os.path.join(path ,filename))
        return 'fail'
def downloadFile(path_filename, sock):
    sock.send('EXISTS ' + str(os.path.getsize(path_filename)))
    print 'EXISTS ' + str(os.path.getsize(path_filename))
    with open(path_filename, 'rb') as f:
        bytesToSend = f.read(1024)
        sock.send(bytesToSend)
        while bytesToSend != "":
            bytesToSend = f.read(1024)
            sock.send(bytesToSend)

            
def removeFile(path, filename, sock):
    os.remove(os.path.join(path, filename))
    sock.send('File %s Removed' % filename)
    
def toTmpFile(path, filename, sock, index):
    os.rename(os.path.join(path, filename), os.path.join(path, (filename + '##' + index + '##tmp')))
    sock.send('File %s Removed (saved as tmp)' % filename)

def mkdir(path, dirName, sock):
    os.mkdir(os.path.join(path, dirName))
    sock.send('Dir %s Created' % dirName)
#def rmdir(path, dirName, sock):
