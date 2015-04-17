import socket
import threading
import os
import string

class dir:
    def __init__(self,user):
        self.user = user
        self.curr = '/'

    def curr_dir():
        return self.curr

    def abs_dir(self, sub_dir):
        if sub_dir == '..':
            if self.curr != '.':
                res = self.curr[1:self.curr.find('/',1)]
            return self.curr[1:]
        elif sub_dir == '.':
            if self.curr == '/':
                return '.'
            else:
                return self.curr[1:]
        elif sub_dir[0] == '/':
            if len(sub_dir) == 1:
                return '.'
            else:
                return sub_dir[1:]
        else:
            res = self.curr+'/' + sub_dir
            return res[1:]

    def update_dir(self, new_dir):
        if new_dir == '.':
            self.curr = '/'
        else:
            self.curr = '/'+new_dir
 
class client:
    def __init__(self, ip, port, client_id, mydir):
        self.ip = ip
        self.port = port
        self.client_id = client_id
        self.mydir = mydir

    def start(self):
        print('Client start...')
        cc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cc.connect((self.ip, self.port))
        
        
        request = 'cd'+' '+self.mydir.curr_dir()
        cc.send(request)
        response == cc.recv(1024)
        if response == 'path invalid':
            print('no such directory.')
        elif response == 'empty':
            print('current directory:'+self.mydir.curr_dir())
            print('files in current directory are:')
        else:
            print('current directory:'+self.mydir.curr_dir())
            print('files in current directory are:')
            print(response)
            
        while True:
            request = raw_input('Please input request:\n')
            words = request.split()
            if words[0] == 'upload':
                absDir = self.mydir.abs_dir(words[1], self.mydir.curr_dir())
                filename = words[2]
                real_file = filename.split('/')
                real_file = real_file[len(real_file)-1]
                request = words[0]+' '+absDir+' '+real_file+' ' + str(os.path.getsize(filename))
                print request
                cc.send(request)
                response = cc.recv(1024)
                if response == 'STOP':
                    print('Oops,Storage service is not available now.')                   
                    continue
                elif response == 'OK':
                    print('Storage sevice is available')
                    with open(filename, 'rb') as f:
                        print '%s opened' % filename
                        bytesToSend = f.read(1024)
                        cc.send(bytesToSend)
                        while bytesToSend != "":
                            bytesToSend = f.read(1024)
                            cc.send(bytesToSend)
                    response = cc.recv(1024)
                    if response == 'path invalid':
                        print('Path invalid')
                    elif response == 'success':
                        print('Upload file successfully.')

            elif words[0] == 'download':
                dest_dir = 'download/'
                absDir = self.mydir.abs_dir(words[1], self.mydir.curr_dir())                
                request = words[0]+' '+absDir+' '+words[2]
                print request
                cc.send(request)
                response = cc.recv(1024)
                if response == 'STOP':
                    print('Oops,Storage service is not available now.')                   
                    continue
                elif response == 'OK':
                    print('Storage sevice is available')
                    filesize = cc.recv(1024)
                    if filesize == 'not exist':
                        print("file doesn't exists")
                        continue
                    elif filesize == 'fail':
                        print("file download fails")
                        continue
                    filesize = long(filesize)
                    with open(dest_dir+words[2], 'wb') as f:
                        data = cc.recv(1024)
                        totalRecv = len(data)
                        f.write(data)
                        while totalRecv < filesize: 
                            print str(totalRecv) + '/' + str(filesize)
                            data = cc.recv(1024)
                            totalRecv += len(data)
                            f.write(data)
                        print "Receive Complete!"
            elif words[0] == 'rm':
                absDir = abs_dir(words[1], self.mydir.curr_dir())                
                request = words[0]+' '+absDir+' '+words[2]
                print request
                cc.send(request)
                response = cc.recv(1024)
                if response == 'STOP':
                    print('Oops,Storage service is not available now.')                   
                    continue
                elif response == 'OK':
                    print('Storage sevice is available')
                    ack = cc.recv(1024)
                    if ack == 'path invalid':
                        print("Path invalid.")
                        continue
                    elif ack == 'success':
                        print("remove file successfully.")
                        continue
            elif words[0] == 'cd':
                absDir = self.mydir.abs_dir(words[1], self.mydir.curr_dir())
                request = 'cd'+' '+absDir
                cc.send(request)
                response == cc.recv(1024)
                if response == 'path invalid':
                    print('no such directory.')
                else:
                    self.mydir.update_dir(absDir)
                    print('current directory:'+self.mydir.curr_dir())
                    print('files in current directory are:')
                    print(response)
                
                
                
        cc.close()

         

def main():
    mydir = dir('simon')
    c1 = client('127.0.0.1',8080,-1,mydir)
    c1.start()



if __name__ == '__main__':
    main()

