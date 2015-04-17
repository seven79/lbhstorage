import socket
import threading
import os
import string


class client:
    def __init__(self, ip, port, client_id):
        self.ip = ip
        self.port = port
        self.client_id = client_id

    def start(self):
        print('Client start...')
        cc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cc.connect((self.ip, self.port))
        
        while True:
            request = raw_input('Please input request:\n')
            words = request.split()
            if words[0] == 'upload':
                path = words[1]
                filename = words[2]
                real_file = filename.split('/')
                real_file = real_file[len(real_file)-1]
                request = (words[0]+' '+words[1]+' '+real_file+' ' + str(os.path.getsize(filename)))
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
            else words[0] == 'download':
                
        cc.close()
         

def main():
    c1 = client('127.0.0.1',8080,-1)
    c1.start()



if __name__ == '__main__':
    main()

