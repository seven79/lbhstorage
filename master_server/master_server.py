import socket
import threading
import os
import string
import config


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

class threadcomm:
    def __init__(self, thread_type):
        self.t_type = thread_type

    def write_message(self,message,node_list):
        if isinstance(node_list,list):
            for i in node_list:
                config.maintain_message[self.t_type][i] = message
                config.mMessage_ready[self.t_type][i] = True
            
        else:
            config.maintain_message[self.t_type][node_list] = message
            config.message_ready[self.t_type][node_list] = True            
            
    def wait_respose(self,node_list):
        ready = False
        if isinstance(node_list,list):
            while not ready:
                ready = config.response_ready[self.t_type][node_list[0]]
                for i in node_list[1:]:
                ready = ready and config.response_ready[self.t_type][i] 
            for i in node_list:
                config.response_ready[self.t_type][i] = False
        else:
            while not ready:
                ready = config.response_ready[self.t_type][node_list]
            config.response_ready[self.t_type][node_list] = False

    def wait_message(self,client_id):
            #wait for message from maintain manage
        while config.message_ready[self.t_type][client_id] == False:
            pass
        config.message_ready[self.t_type][client_id] == False        

    def get_message(self,client_id):
        return config.message[self.t_type][client_id]

class server:      
    def __init__(self, server_type, ip='127.0.0.1', port=8000):          
        self.ip = ip  
        self.port = port  
        self.server_type = server_type
        self.client_num = 0
      
    def start(self):          
        print("Server start({0}:{1})...".format(self.ip, self.port))  
                  
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ss.settimeout(1000 * 10)  
        ss.bind((self.ip, self.port))  
        ss.listen(5)  
          
        while True:  
            (client, address) = ss.accept()  
            #receive identity message from client
            client_id = string.atoi(client.recv(1024))
            #refresh the state table
            config.STATE_TABLE[self.server_type][client_id] = True
            print(config.STATE_TABLE)
            self.client_num += 1
            print("client connecting:",self.client_num)  
            handler = Handler(self.server_type, client_id)
            handler.setConnect(client)  
            handler.start()  
        ss.close()  
        print(self.server_type + "Server close, bye-bye.") 

class client:
    def __init__(self, ip, port, client_id):
        self.ip = ip
        self.port = port
        self.client_id = client_id

    def start(self):
        print('Client start...')
        cc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cc.connect((self.ip, self.port))
        cc.send(str(self.client_id))
        print(config.STATE_TABLE['service'])
    

class Handler(threading.Thread):  
    def __init__(self, name, client_id):
        threading.Thread.__init__(self)
        self.t_name = name
        self.client_id = client_id

    def setConnect(self, connect):  
        self.connect = connect  
      
    def run(self):   
        if self.t_name == 'service':
            print('Start service server handler!')

        elif self.t_name =='maintain':
            print('Start maintain server handler!')
            maintain_handler()

    def maintain_handler(self):
        while True:
            tc = threadcomm(self.t_name)
            tc.wait_message()
            #parse the message send by maintain manage
            command = tc.get_message(self.client_id).split() 
            #switch to certain handler 
            switcher(command, self.connect, self.client_id, self.t_name)
                

class manage(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.t_name = name

    def run(self):
        if self.t_name == 'maintain':
            maintain_manager()
        elif self.t_name == 'service':
            service_manager()


    def maintain_manager():
        mylog = log('master_server.log')
        while True:
            valid_list=[]
            invalid_list=[]
            node_list=[] 
            #check if connected clients >= 2, if <2 stuck in while loop and wait
            while len(node_list) < 2:
                del node_list[:]
                for i in range(3):
                    if config.STATE_TABLE['maintain'][i] == True:
                        node_list.append(i)
            #if connected clients >=2, start service and recovery nodes
            #check which node need to recovery by compare latest index 
            query_index(node_list)
            for i in node_list:
                if config.latest_index[i] == mylog.get_latest_index():
                    valid_list.append(i)
                else: 
                    invalid_list.append(i)
            for i in invalid_list:
                while config.latest_index[i] < mylog.get_latest_index():
                    recovery(i, valid_list[0], config.latest_index[i]+1, mylog)
              
    
def recovery(recovery_node,helper_node, index, mylog):
    curr_log = mylog.read_log(index).split()
    cmd = curr_log[1] 
    if cmd == 'upload':
        download_file(helper_node, curr_log[2], curr_log[3], curr_log[0], 'maintain')
        upload_file(recovery_node, curr_log[2], curr_log[3], 'maintain_upload/'+filename, 'maintain')
        os.remove('maintain_upload'+filename)
    

    
        

def query_index(node_list,server_type):
    tc = threadcomm(server_type)
    tc.write_message('index',node_list)
    tc.wait_respose(node_list)

def upload_file(node_list, dest_dir, filename, src_dir,server_type):
    src_dir = src_dir + filename
    if os.path.isfile(src_dir):
        filesize = os.path.getsize(src_dir)

    tc = threadcomm(server_type)
    tc.write_message('upload '+dest_dir+' '+filename+' '+filesize, node_list)

    tc.wait_respose(node_list)
    else:
        print('upload '+src_dir+' error: no such file.')
  
def download_file(node_list, src_dir, filename, index, server_type):
    tc = threadcomm(server_type)
    tc.write_message('download '+src_dir+' '+ filename + ' ' + index, node_list)

    tc.wait_respose(node_list)


def switcher(cmd,connect,client_id,t_name):
    switch = {'index': handle_index
              'upload': handle_upload
              'download': handle_download
          }
    switch[cmd[0]](cmd,connect,client_id,t_name)


def handle_index(cmd,connect,client_id,server_type):
    connect.send(cmd[0])
    config.latest_index[client_id] = connect.recv(1024)
    config.action_result[server_type][client_id] = True
    config.response_ready[server_type][client_id] = True

def handle_upload(cmd,connect,client_id,server_type):
    connect.send(cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]) #upload dest_dir file_name file_size
    ack = connect.recv(1024)
    if ack == 'Path invalid':
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id] = True
        return

    elif ack == 'OK':
        with open(cmd[4],'rb') as f: #cmd[4] is src_dir
            bytesToSend = f.ready(1024)
            connect.send(bytesToSend)
            while bytesToSend != "":
                bytesToSend = f.read(1024)
                connect.send(bytesToSend)
        #recive commit from client
        commit = connect.recv(1024)
        if commit == 'OK':
            if server_type == 'maintain':
                #if it's maintain server, no need to gather 2/3 commits
                connect.send('OK')
            config.action_result[server_type][client_id] = True
        else:
            config.action_result[server_type][client_id] = False

        config.response_ready[server_type][client_id] = True

def handle_download(cmd,connect,client_id,server_type):
    connect.send(cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]) #download src_dir file_name index
    res = connect.recv(1024)
    res = res.split()
    if res[0] == 'EXISTS':
        print 'file exists'
        size = long(res[1])
        if server_type=='maintain':
            path = 'maintain_upload/'
        elif: server_type == 'service':
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
            


