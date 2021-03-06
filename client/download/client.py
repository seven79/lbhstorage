import socket
import threading
import os
import string

class dir:
    def __init__(self,user):
        self.user = user
        self.curr = '/'

    def curr_dir(self):
        return self.curr

    def abs_dir(self, sub_dir):
        if sub_dir == '..':
            if self.curr != '/':
                res = self.curr[:self.curr.rfind('/')]
                if res == '':
                    return '.'
                else:
                    return res[1:]
            else: 
                return '.'
                    
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
            if self.curr == '/':
                res = self.curr + sub_dir
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
        #create download directory
        path = ('download')
        if os.path.exists(path) == False:
            os.mkdir(path)

        cc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cc.connect((self.ip, self.port))
        
        
        request = 'cd'+' '+'.'
        cc.send(request)
        response = cc.recv(1024)
        if response == 'STOP':
            print('Oops,Storage service is not available now.')                   
        elif response == 'OK':
            print('Storage sevice is available')

            response = cc.recv(1024)
            if response == 'path invalid':
                print('no such directory.')
            else:
                print('current directory:'+self.mydir.curr_dir())
                print('files in current directory are:')
                print(response)
            
        while True:
            request = raw_input('Please input request:\n')
            words = request.split()
            if words[0] == 'upload':
                if len(words) != 3:
                    print('Try again! Correct format: upload absolute_path/relative_path filename')
                    continue
                else:
                    absDir = self.mydir.abs_dir(words[1])
                    if os.path.isfile(words[2])!=True:
                        print ('No such file:'+ words[2])
                        continue
                    else:
                        filename = words[2]
                        real_file = filename.split('/')
                        real_file = real_file[len(real_file)-1]
                        request = words[0]+' '+absDir+' '+real_file+' ' + str(os.path.getsize(filename))

                        cc.send(request)
                        response = cc.recv(1024)
                        if response == 'STOP':
                            print('Oops,Storage service is not available now.')                   
                            continue
                        elif response == 'OK':
                            print('Storage sevice is available')
                            with open(filename, 'rb') as f:

                                bytesToSend = f.read(1024)
                                cc.send(bytesToSend)
                                while bytesToSend != "":
                                    bytesToSend = f.read(1024)
                                    cc.send(bytesToSend)
                            response = cc.recv(1024)
                            if response == 'path invalid':
                                print('Path invalid')
                            elif response == 'file exists':
                                print('File already exists')
                            elif response == 'success':
                                print('Upload file successfully.')
                                    
            elif words[0] == 'download':
                if len(words) != 3:
                    print ('Try again! Correct format: download absolute_path/relative_path filename')
                    continue
                else:
                    dest_dir = 'download/'
                    absDir = self.mydir.abs_dir(words[1])                
                    request = words[0]+' '+absDir+' '+words[2]

                    cc.send(request)
                    response = cc.recv(1024)
                    if response == 'STOP':
                        print('Oops,Storage service is not available now.')                   
                        continue
                    elif response == 'OK':
                        print('Storage sevice is available')
                        filesize = cc.recv(1024)
                        if filesize == 'not exist':
                            print("File doesn't exists")
                            continue
                        elif filesize == 'fail':
                            print("File download fails")
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
                            print "Download Complete!"
                                

            elif words[0] == 'rm':
                if len(words) != 2:
                    print('Try again! Correct format: rm filename')
                    continue
                else:
                    absDir = self.mydir.abs_dir('.')                
                    request = words[0]+' '+absDir+' '+words[1]

                    cc.send(request)
                    response = cc.recv(1024)
                    if response == 'STOP':
                        print('Oops,Storage service is not available now.')                   
                        continue
                    elif response == 'OK':
                        print('Storage sevice is available')
                        ack = cc.recv(1024)
                        if ack == 'not exist':
                            print('File does not exist.')
                            continue
                        if ack == 'not file':
                            print(words[1]+' is not a file')
                            continue
                        elif ack == 'success':
                            print("Remove file successfully.")
            
            
            elif words[0] == 'cd':
                if len(words) != 2:
                    print('Try again! Correct format: cd absolute_path/relative path')
                    continue
                else:
                    absDir = self.mydir.abs_dir(words[1])
                    request = 'cd'+' '+absDir
                    cc.send(request)
                    response = cc.recv(1024)
                    if response == 'STOP':
                        print('Oops,Storage service is not available now.')                   
                        continue
                    elif response == 'OK':
                        print('Storage sevice is available')

                    response = cc.recv(1024)
                    if response == 'path invalid':
                        print('No such directory.')
                    else:
                        self.mydir.update_dir(absDir)
                        print('Current directory:'+self.mydir.curr_dir())
                        print('Files in current directory are:')
                        print(response)

            elif words[0] == 'ls':
                if len(words) != 1:
                    print('Try again! Correct format: ls')
                    continue
                else:
                    absDir = self.mydir.abs_dir('.')
                    request = 'cd'+' '+absDir
                    cc.send(request)
                    response = cc.recv(1024)
                    if response == 'STOP':
                        print('Oops,Storage service is not available now.')                   
                        continue
                    elif response == 'OK':
                        print('Storage sevice is available')

                    response = cc.recv(1024)
                    if response == 'path invalid':
                        print('No such directory.')
                    else:
                        self.mydir.update_dir(absDir)
                        print('Current directory:'+self.mydir.curr_dir())
                        print('Files in current directory are:')
                        print(response)

            elif words[0] == 'mkdir':
                if len(words) != 2:
                    print ('Try again! Correct format: mkdir directory_name')
                    continue
                else:
                    absDir = self.mydir.abs_dir('.')                
                    request = words[0]+' '+absDir+' '+words[1]

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
                        if ack == 'exists':
                            print("Directory already exists.")
                            continue
                        elif ack == 'success':
                            print("Create directory successfully.")
        
            elif words[0] == 'rmdir':
                if len(words) != 2 :
                    print('Try again! Correct format: rmdir absolute_path/relative_path')
                    continue
                else:
                    absDir = self.mydir.abs_dir(words[1])                
                    request = words[0]+' '+absDir

                    cc.send(request)
                    response = cc.recv(1024)
                    if response == 'STOP':
                        print('Oops,Storage service is not available now.')                   
                        continue
                    elif response == 'OK':
                        print('Storage sevice is available')
                        ack = cc.recv(1024)
                        if ack == 'not exist':
                            print("Directory does not exist.")
                            continue
                        elif ack == 'not empty':
                            print("Directory is not empty, you must remove all the files under it before remove directory.")
                        elif ack == 'not dir':
                            print(words[1]+" is not a directory")
                        elif ack == 'success':
                            print("Remove directory successfully.")
                
            elif words[0] == 'exit':
                if len(words) != 1 :
                    print('Try again! Correct format: exit')
                    continue
                cc.send('exit')
                break

                
            else:
                print('no such command: '+words[0])
                
        cc.close()

         

def main():
    mydir = dir('simon')
    c1 = client('127.0.0.1',8080,-1,mydir)
    c1.start()



if __name__ == '__main__':
    main()

