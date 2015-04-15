import socket
import threading
import os
import string
import config
import time


class log:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename) as f:
            self.filelines = len(f.readlines())

    def append(self, message):
        with open(self.filename,'a') as f:
            f.write(message+'\n')
        self.filelines += 1
    
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
        

class threadcomm:
    def __init__(self, thread_type):
        self.t_type = thread_type

    def write_message(self,message,node_list):
        if isinstance(node_list,list):
            for i in node_list:
                config.message[self.t_type][i] = message
                config.message_ready[self.t_type][i].set()
            
        else:
            config.message[self.t_type][node_list] = message
            config.message_ready[self.t_type][node_list].set()            
            
    def wait_response(self,node_list):
        if isinstance(node_list,list):
            for i in node_list:
                config.response_ready[self.t_type][i].wait() 
            for i in node_list:
                config.response_ready[self.t_type][i].clear()
        else:
            config.response_ready[self.t_type][node_list].wait()
            config.response_ready[self.t_type][node_list].clear()

    def wait_message(self,client_id):
        #wait for message from maintain manage
        config.message_ready[self.t_type][client_id].wait()
        config.message_ready[self.t_type][client_id].clear()        

    def get_message(self,client_id):
        return config.message[self.t_type][client_id]

class server:      
    def __init__(self, server_type, ip='127.0.0.1', port=8000):          
        self.ip = ip  
        self.port = port  
        self.server_type = server_type
        self.client_num = 0
        print(self.server_type+' created.')
      
    def start(self):          
        print(self.server_type+" server start({0}:{1})...".format(self.ip, self.port))  
                  
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ss.settimeout(1000 * 10)  
        ss.bind((self.ip, self.port))  
        ss.listen(5)  
          
        while True:  
            (client, address) = ss.accept()  
            if self.server_type == 'maintain' or self.server_type == 'service':
                #receive identity message from client
                client_id = string.atoi(client.recv(1024))
                #refresh the state table
                config.STATE_TABLE[self.server_type][client_id] = True
                print(self.server_type+' '+str(client_id)+' connected.')
                handler = Handler(self.server_type, client_id)
            elif self.server_type == 'client':
                handler = Handler(self.server_type)
            self.client_num += 1
            print("client connecting:",self.client_num)  
            handler.setConnect(client)  
            handler.start()  
        ss.close()  
        print(self.server_type + "Server close, bye-bye.") 
    

class Handler(threading.Thread):  
    def __init__(self, name, client_id=-1):
        threading.Thread.__init__(self)
        self.t_name = name
        self.client_id = client_id
        self.log = log('master_server.log')

    def setConnect(self, connect):  
        self.connect = connect  
      
    def run(self):   
        if self.t_name == 'service' or self.t_name == 'maintain':
            print('Start '+self.t_name+' server handler!')
            self.ms_handler()
        elif self.t_name =='client':
            print('Start client server handler!')
            self.client_handler()

    #handler for maintain and service server
    def ms_handler(self):
        tc = threadcomm(self.t_name)
        while True:
            tc.wait_message(self.client_id)
            #parse the message send by maintain manage
            command = tc.get_message(self.client_id).split() 
            #switch to certain handler 
            switcher(command, self.connect, self.client_id, self.t_name)

    #handler for client server
    def client_handler(self):
        while True:
            #receive request from client
            request = self.connect.recv(1024)
            #check if now there are at least 2 node connected to service server
            node_list = []
            valid_list = []
            for i in range(3):
                if config.STATE_TABLE['service'][i] == True:
                        node_list.append(i)

            print('node list:'+str(node_list))
            #if connected nodes < 2, stop service
            if len(node_list) < 2:
                self.connect.send('STOP')
                print('Received request, but there are not enough nodes connected.')
                continue
            #if node_list >= 2, check now many node has latest log
            latest_index=query_index(node_list,'service')
            for i in node_list:
              if latest_index[i] == self.log.get_latest_index():
                  valid_list.append(i)
                  
            print('valid list:'+str(valid_list))
            #if valid node < 2, stop service
            if len(valid_list) < 2:
                self.connect.send('STOP')
                print('Enough connected nodes, but not enough valid nodes.')
                continue
            #if connected nodes >=2 and valid node >=2,start handle request
            self.connect.send('OK')
            #command is a list, is parsed request
            command = request.split()
            #new_index = self.log.get_latest_index()+1
            if command[0] == 'upload':
                receive_file(command,self.connect)
                upload_file(valid_list,command[1],command[2],'service_upload/', 'service')
                os.remove('service_upload/'+command[2])

            elif command[0] == 'download':
                download_file(valid_list, command[1], command[2], str(-1), 'service')
                send_file(command,'service_download/',self.connect)
                os.remove('service_download/'+command[2])
            
    
                

class manage(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.t_name = name
        self.log = log('master_server.log')

    def run(self):
        print('maintain server manager start.')
        while True:
            valid_list=[]
            invalid_list=[]
            node_list=[] 
            #check if connected clients >= 2, if <2 stuck in while loop and wait
            while len(node_list) < 2:
                time.sleep(5)
                del node_list[:]
                for i in range(3):
                    if config.STATE_TABLE['maintain'][i] == True:
                        node_list.append(i)
                if len(node_list) >= 2:
                    break
                print('maintain server manager: not enough connected nodes.')
                    
            print('maintain server manager: enough connected nodes.')
            #if connected clients >=2, start service and recovery nodes
            #check which node need to recovery by compare latest index 
            latest_index = query_index(node_list,'maintain')
            print('latest_index: '+str(latest_index))
            my_index = self.log.get_latest_index()
            print('my_index is '+str(my_index))
            for i in node_list:
                if latest_index[i] == self.log.get_latest_index():
                    valid_list.append(i)
                else: 
                    invalid_list.append(i)
            print('maintain server manager: valid node is' + str(valid_list) + ' invalid node is '+str(invalid_list))
            for i in invalid_list:
                while config.latest_index[i] < self.log.get_latest_index():
                    recovery(i, valid_list[0], config.latest_index[i]+1, self.log)
            #check every 5s
            time.sleep(5)
                    
                                  
    
def recovery(recovery_node,helper_node, index, mylog):
    print('start recovery node '+str(recovery_node)+', helper is '+str(helper_node))
    curr_log = mylog.read_log(index).split()
    cmd = curr_log[1] 
    if cmd == 'upload':
        download_file(helper_node, curr_log[2], curr_log[3], curr_log[0], 'maintain')
        upload_file(recovery_node, curr_log[2], curr_log[3], 'maintain_upload/'+filename, 'maintain')
        os.remove('maintain_upload'+filename)
    

    
        

def query_index(node_list,server_type):
    tc = threadcomm(server_type)
    tc.write_message('index',node_list)
    tc.wait_response(node_list)
    return config.latest_index

def upload_file(node_list, dest_dir, filename, src_dir,server_type):
    src_dir = src_dir + filename
    if os.path.isfile(src_dir):
        filesize = os.path.getsize(src_dir)

        tc = threadcomm(server_type)
        tc.write_message('upload '+dest_dir+' '+filename+' '+str(filesize), node_list)
        
        tc.wait_response(node_list)
        #check if at least 2 nodes reply commit
        count = 0
        for i in node_list:
           if config.action_result[server_type][i] == True:
               count += 1
        if count >= 2:
            tc.write_message('ack',node_list)
            tc.wait_response(node_list)
        else:
            tc.write_message('fail',node_list)
            tc.wait_response(node_list)
            
        
    else:
        print('upload '+src_dir+' error: no such file.')
  
def download_file(node_list, src_dir, filename, index, server_type):
    tc = threadcomm(server_type)
    tc.write_message('download '+src_dir+' '+ filename + ' ' + index, node_list)

    tc.wait_response(node_list)


def switcher(cmd,connect,client_id,t_name):
    switch = {'index': handle_index,
              'upload': handle_upload,
              'download': handle_download,
              'ack': handle_ack,
              'fail': handle_fail,
          }
    switch[cmd[0]](cmd,connect,client_id,t_name)


def handle_index(cmd,connect,client_id,server_type):
    connect.send(cmd[0])
    config.latest_index[client_id] = string.atoi(connect.recv(1024))
    config.action_result[server_type][client_id] = True
    config.response_ready[server_type][client_id].set()

def handle_upload(cmd,connect,client_id,server_type):
    connect.send(cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]) #upload dest_dir file_name file_size
    ack = connect.recv(1024)
    if ack == 'Path invalid':
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return

    elif ack == 'OK':
        with open(cmd[4],'rb') as f: #cmd[4] is src_dir
            bytesToSend = f.read(1024)
            connect.send(bytesToSend)
            while bytesToSend != "":
                bytesToSend = f.read(1024)
                connect.send(bytesToSend)
        #recive commit from client
        commit = connect.recv(1024)
        if commit == 'commit':
            if server_type == 'maintain':
                #if it's maintain server, no need to gather 2/3 commits
                connect.send('ACK')
            config.action_result[server_type][client_id] = True
        else:
            config.action_result[server_type][client_id] = False
            
        config.response_ready[server_type][client_id].set()

def handle_download(cmd,connect,client_id,server_type):
    if server_type == 'maintain':
        connect.send(cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]) #download src_dir file_name index
    elif server_type == 'service':
        connect.send(cmd[0]+' '+cmd[1]+' '+cmd[2]) #download src_dir file_name
    res = connect.recv(1024)
    res = res.split()
    if res[0] == 'EXISTS':
        print 'file exists'
        size = long(res[1])
        if server_type=='maintain':
            path = 'maintain_upload/'
        elif server_type == 'service':
            path = 'service_download/'
            
        with open(path+filename, 'wb') as f:
            data = connect.recv(1024)
            totalRecv = len(data)
            f.write(data)
            while totalRecv < size: 
                print str(totalRecv) + '/' + str(size)
                data = sock.recv(1024)
                totalRecv += len(data)
                f.write(data)
            print "Download Complete!"
    else:
        print 'No such file'

def handle_ack(connect,client_id,server_type):
    connect.send('ACK')
    config.action_result[server_type][client_id] = True  
    config.response_ready[server_type][client_id] = True

def handle_fail(connect,client_id,server_type):
    connect.send('FAIL')
    config.action_result[server_type][client_id] = True  
    config.response_ready[server_type][client_id] = True


def receive_file(cmd,connect):
    size = long(cmd[3])
    with open('service_upload/'+cmd[2], 'wb') as f:
        data = connect.recv(1024)
        totalRecv = len(data)
        f.write(data)
        while totalRecv < size: 
            print str(totalRecv) + '/' + str(size)
            data = connect.recv(1024)
            totalRecv += len(data)
            f.write(data)
        print "Receive Complete!"
    
def send_file(cmd, src_dir, connect):
    src_dir = src_dir + cmd[2] #cmd=[download src_dir filename]
    if os.path.isfile(src_dir):
        filesize = os.path.getsize(src_dir)
    #send filesize to client
    connect.send(str(filesize))

    with open(src_dir,'rb') as f:
        bytesToSend = f.ready(1024)
        connect.send(bytesToSend)
        while bytesToSend != "":
            bytesToSend = f.read(1024)
            connect.send(bytesToSend)

    print('Send Complete!')


def main():
    maintain_server_manager = manage('maintain')
    maintain_server_manager.setDaemon(True)
    service_server = server('service','127.0.0.1',8000)
    maintain_server = server('maintain','127.0.0.1',8001)
    client_server = server('client', '127.0.0.1', 8080)
    ss = threading.Thread(target = service_server.start)
    ss.setDaemon(True)
    ms = threading.Thread(target = maintain_server.start)
    ms.setDaemon(True)
    #start maintain server manager
    maintain_server_manager.start()    
    #start maintain server
    ms.start()
    #start service server
    ss.start()
    #start client server ps:client server is not a new thread
    client_server.start()
    
if __name__ == '__main__':
    main()
