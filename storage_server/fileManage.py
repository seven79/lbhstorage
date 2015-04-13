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
        
