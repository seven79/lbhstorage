B1;3409;0cimport socket
import threading
import os
import string
import config


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
            if(config.STATE_TABLE['valid'][client_id]) 
            print('Start service server handler!')

        elif self.t_name =='maintain':
            print('Start maintain server handler!')

    def maintain_handler(self):
        while True:
            #wait for message from maintain manage
            while config.message_ready[self.client_id] == False :
                pass
            config.message_ready[self.client_id] == False
            #parse the message send by maintain manage
            command = config.maintain_message[self.client_id].split() 
            #switch to certain handler 
            switcher(command, self.connect, self.client_id)
                
def switcher(cmd,connect,client_id):
    switch = {'index': handle_index
              'upload': handle_upload
              'download': handle_download
          }
    switch[cmd[0]](cmd,connect,client_id)

    #send message to node and receive the latest index
def handle_index(cmd,connect,client_id):
    connect.send(cmd[0])
    config.latest_index[client_id] = connect.recv(1024)
    config.action_result[client_id] = True
    config.response_ready[client_id] == True

def handle_upload(cmd,connect,client_id):
    connect.send(cmd[0])
    ack = connect.recv(1024)
    if ack == 'Path invalid':
        config.action_result[client_id] = False
    elif ack == 'OK':
        
    config.response_ready[self.client_id] == True

class manage(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.t_name = name

    def run(self):
        if self.t_name == 'maintain':
            



def latest_index(node_list):
    write_message('index', node_list)
    
    wait_respose(node_list)

def upload_file(node_list, dest_dir, filename):
    write_message('upload '+dest_dir+' '+filename, node_list)

    wait_respose(node_list)

def download_file(node_list, src_dir, filename):
    write_message('download '+src_dir+' '+ filename, node_list)

    wait_respose(node_list)

def write_message(message,node_list):
    for i in node_list:
        config.maintain_message[i] = message
        config.message_ready[i] = True

def wait_respose(node_list):
    ready = False
    while not ready:
        ready = config.response_ready[node_list[0]]
        for i in node_list[1:]:
            ready = ready and config.response_ready[i] 
    config.response_ready[0] = False
    config.response_ready[1] = False
    config.response_ready[2] = False

