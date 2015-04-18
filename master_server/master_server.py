import socket
import threading
import os
import string
import config
import time
import errno


class log:
    def __init__(self, filename):
        self.filename = filename

    def append(self, message):
        if message == '':
            return
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
            if words[len(words) - 1] == 'uncommitted':
                self.delete_last_line()        

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
                client_id = recv_msg(client,-1,'master')
                if client_id == '':
                    continue
                else:
                    client_id = string.atoi(client_id)
                #refresh the state table
                config.STATE_TABLE[self.server_type][client_id] = True
                print(self.server_type+' '+str(client_id)+' connected.')
                handler = Handler(self.server_type, client_id)
            elif self.server_type == 'client':
                handler = Handler(self.server_type)
            self.client_num += 1
            print("client connecting:",self.client_num)  
            handler.setConnect(client)  
            handler.setDaemon(True)
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
            #if current node disconnect, quit the handler
            if config.STATE_TABLE[self.t_name][self.client_id] == False:
                break

    #handler for client server
    def client_handler(self):
        while True:
            #receive request from client
            request = recv_msg(self.connect,-1,'master')
            if request == '':
                self.connect.close()
                break

            #--------check if now there are at least 2 node connected to service server-------------
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

            #----------check now many node has latest log(valid)----------------
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


            #----------handle upload request----------------
            if command[0] == 'upload':
                receive_file(command,self.connect)
                if upload_file(valid_list,command[1],command[2],'service_upload/', 'service') == False:
                    if config.error_message['service'][valid_list[0]] == 'path invalid':
                        self.connect.send('path invalid')
                else:
                    self.connect.send('success')
                
                    
                os.remove('service_upload/'+command[2])

            #----handle download request----------------
            elif command[0] == 'download':
                if download_file(valid_list[0], command[1], command[2], str(-1), 'service') == True:
                    send_file(command,'service_download/',self.connect)
                    os.remove('service_download/'+command[2])
                else:
                    if config.error_message['service'][valid_list[0]] == 'not exist':
                        if send_msg('not exist',self.connect,-1,'client') == False:
                            print('client disconnect.')
                            self.connect.close()
                            break
                    else:
                        if send_msg('fail',self.connect,-1,'client') == False:
                            print('client disconnect.')
                            self.connect.close()
                            break
            #-------handle rm request---------------------
            elif command[0] == 'rm':
                if remove_file(valid_list, command[1], command[2], 'service') == False:
                    if config.error_message['service'][valid_list[0]] == 'path invalid':
                        self.connect.send('path invalid')
                else:
                    self.connect.send('success')
            #--------handle cd request---------------------
            elif command[0] == 'cd':
                if cd(valid_list[0], command[1], 'service') == False:
                    if config.error_message['service'][valid_list[0]] == 'path invalid':
                        self.connect.send('path invalid')
                else:
                    self.connect.send(config.curr_dir)

            #---------handle mkdir request----------------
            elif command[0] == 'mkdir':
                if mkdir(valid_list, command[1], command[2], 'service') == False:
                    if config.error_message['service'][valid_list[0]] == 'path invalid':
                        self.connect.send('path invalid')
                    elif config.error_message['service'][valid_list[0]] == 'Directory already exists':
                        self.connect.send('exists')
                else:
                    self.connect.send('success')

             #-------handle rmdir request---------------------
            elif command[0] == 'rmdir':
                if remove_dir(valid_list, command[1],  'service') == False:
                    if config.error_message['service'][valid_list[0]] == 'not exist':
                        self.connect.send('not exist')
                    elif config.error_message['service'][valid_list[0]] == 'not empty':
                        self.connect.send('not empty')
                else:
                    self.connect.send('success')

            

             
                    
                    
            
    
                

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
            print(config.STATE_TABLE)
            while len(node_list) < 2:
                time.sleep(5)
                del node_list[:]
                for i in range(3):
                    if config.STATE_TABLE['maintain'][i] == True:
                        node_list.append(i)
                print('node_list: '+str(node_list))
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
                    config.latest_index[i] += 1
            #check every 5s
            time.sleep(5)
                    
                                  
    
def recovery(recovery_node,helper_node, index, mylog):
    print('start recovery node '+str(recovery_node)+', helper is '+str(helper_node))
    curr_log = mylog.read_line(index).split()
    cmd = curr_log[1] 
    if cmd == 'upload':
        download_file(helper_node, curr_log[2], curr_log[3], curr_log[0], 'maintain')
        upload_file(recovery_node, curr_log[2], curr_log[3], 'maintain_upload/', 'maintain')
        os.remove('maintain_upload/'+curr_log[3])
    elif cmd == 'rm':
        remove_file(recovery_node, curr_log[2], curr_log[3], 'maintain')
    elif cmd == 'rmdir':
        remove_dir(recovery_node, curr_log[2], 'maintain')
    elif cmd == 'mkdir':
        mkdir(recovery_node, curr_log[2], curr_log[3], 'maintain')
        
    

    
#------------Functions managers use to send request to 3 handler connected by 3 nodes       
#------------------------------------------------------------------------------------

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
        
    
        if server_type == 'maintain':
            if config.action_result[server_type][node_list] == False:
                return False
            
        if server_type == 'service':
            #check if at least 2 nodes reply commit
            new_node_list = []
            for i in node_list:
                if config.action_result[server_type][i] == True:
                    new_node_list.append(i)

            if len(new_node_list) == 0:
                return False

            two_phase_commit(tc, new_node_list)
            #write log
            retrive_log(tc,new_node_list)
        return True
                
    else:
        print('upload '+src_dir+' error: no such file.')
  
def download_file(node_list, src_dir, filename, index, server_type):
    tc = threadcomm(server_type)
    tc.write_message('download '+src_dir+' '+ filename + ' ' + index, node_list)

    tc.wait_response(node_list)
    return config.action_result[server_type][node_list]
    
def remove_file(node_list, path, filename, server_type):
    tc = threadcomm(server_type)
    tc.write_message('rm'+' '+path+' '+filename, node_list)
    tc.wait_response(node_list)

    if server_type == 'maintain':
        if config.action_result[server_type][node_list] == False:
            return False

        
    if server_type == 'service':
        #check if at least 2 nodes reply commit
        new_node_list = []
        for i in node_list:
            if config.action_result[server_type][i] == True:
                new_node_list.append(i)
            
        if len(new_node_list) == 0:
            return False

        two_phase_commit(tc, new_node_list)
        #write log
        retrive_log(tc,new_node_list)
    return True

def remove_dir(node_list, path, server_type):
    tc = threadcomm(server_type)
    tc.write_message('rmdir'+' '+path, node_list)
    tc.wait_response(node_list)

    if server_type == 'maintain':
        if config.action_result[server_type][node_list] == False:
            return False
        
    if server_type == 'service':
        #check if at least 2 nodes reply commit
        new_node_list = []
        for i in node_list:
            if config.action_result[server_type][i] == True:
                new_node_list.append(i)
            
        if len(new_node_list) == 0:
            return False

        two_phase_commit(tc, new_node_list)
        #write log
        retrive_log(tc,new_node_list)
    return True


def cd(node_list, dir, server_type):
    tc = threadcomm(server_type)
    tc.write_message('cd'+' '+dir, node_list)
    tc.wait_response(node_list)

    if config.action_result[server_type][node_list] == False:
        return False
    return True

def mkdir(node_list, dir, dir_name, server_type):
    tc = threadcomm(server_type)
    tc.write_message('mkdir'+' '+dir+' '+dir_name, node_list)
    tc.wait_response(node_list)

    if server_type == 'maintain':
        if config.action_result[server_type][node_list] == False:
            return False
        
    if server_type == 'service':
        #check if at least 2 nodes reply commit
        new_node_list = []
        for i in node_list:
            if config.action_result[server_type][i] == True:
                new_node_list.append(i)
            
        if len(new_node_list) == 0:
            return False

        two_phase_commit(tc, new_node_list)
        #write log
        retrive_log(tc,new_node_list)
    return True
    



def switcher(cmd,connect,client_id,t_name):
    switch = {'index': handle_index,
              'upload': handle_upload,
              'download': handle_download,
              'ack': handle_ack,
              'fail': handle_fail,
              'log': handle_log,
              'rm': handle_remove,
              'cd': handle_cd,
              'mkdir': handle_mkdir,
              'rmdir': handle_rmdir,
          }
    switch[cmd[0]](cmd,connect,client_id,t_name)

#---------------------Funcitons used by each handler to communicate with one node-------------------
#---------------------------------------------------------------------------------------------------

def handle_index(cmd,connect,client_id,server_type):
     
    if send_msg(cmd[0],connect,client_id,server_type) == False:
        return

    latest_index = recv_msg(connect, client_id, server_type)
    if latest_index == '':
        return
    else:
        config.latest_index[client_id] = string.atoi(latest_index)

    config.action_result[server_type][client_id] = True
    config.response_ready[server_type][client_id].set()

def handle_upload(cmd,connect,client_id,server_type):
  
  
    if server_type == 'service':
        src_dir = 'service_upload/'
    elif server_type == 'maintain':
        src_dir = 'maintain_upload/'

    msg = cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]  
    print(msg)

    #upload dest_dir file_name file_size  
    if send_msg(msg,connect,client_id,server_type) == False:
        return
    

    ack = recv_msg(connect, client_id, server_type)
    if ack == '':
        return
    
    if ack == 'Path invalid':
        print('Upload: Path invalid.')
        config.error_message[server_type][client_id] = 'path invalid'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return

    elif ack == 'OK':
        with open(src_dir+cmd[2],'rb') as f: #src_dic+filename
            bytesToSend = f.read(1024)

            
            if send_msg(bytesToSend,connect,client_id,server_type) == False:
                return

            while bytesToSend != "":
                bytesToSend = f.read(1024)
                if send_msg(bytesToSend,connect,client_id,server_type) == False:
                    return
        print('Upload Completed.')
        #recive commit from client
        commit = recv_msg(connect,client_id, server_type)
        if commit == '':
            return

        if commit == 'commit':
            print('Upload: receive commit')
            if server_type == 'maintain':
                #if it's maintain server, no need to gather 2/3 commits
                if send_msg('ACK',connect,client_id,server_type) == False:
                    return
            config.action_result[server_type][client_id] = True
        else:
            print('Upload: not receive commit')
            config.action_result[server_type][client_id] = False
            
        config.response_ready[server_type][client_id].set()

def handle_download(cmd,connect,client_id,server_type):
    if server_type == 'maintain':
        #download src_dir file_name index
        msg = cmd[0]+' '+cmd[1]+' '+cmd[2]+' '+cmd[3]
        if send_msg(msg,connect,client_id,server_type) == False:
            return
    elif server_type == 'service':
        #download src_dir file_name
        msg = cmd[0]+' '+cmd[1]+' '+cmd[2]
        if send_msg(msg,connect,client_id,server_type) == False:
            return
    res = recv_msg(connect, client_id, server_type)
    if res == '':
        return
    res = res.split()
    if res[0] == 'EXISTS':
        print 'file exists'
        size = long(res[1])
        if server_type=='maintain':
            path = 'maintain_upload/'
        elif server_type == 'service':
            path = 'service_download/'
            
        with open(path+cmd[2], 'wb') as f:
            data = recv_msg(connect, client_id, server_type)
            if data == '':
                return
                
            totalRecv = len(data)
            f.write(data)
            while totalRecv < size: 
                print str(totalRecv) + '/' + str(size)
                data = recv_msg(connect,client_id, server_type)
                if data == '':
                    return
                totalRecv += len(data)
                f.write(data)
            print "Download Complete!"
        config.action_result[server_type][client_id] = True
        config.response_ready[server_type][client_id].set()
        return

    else:
        print 'No such file'
        config.error_message[server_type][client_id] = 'not exist'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return


def handle_ack(cmd,connect,client_id,server_type):
    if send_msg('ACK',connect, client_id, server_type) == False:
        return
    config.action_result[server_type][client_id] = True  
    config.response_ready[server_type][client_id].set()

def handle_fail(cmd,connect,client_id,server_type):
    if send_msg('FAIL',connect, client_id, server_type) == False:
        return
    config.action_result[server_type][client_id] = True  
    config.response_ready[server_type][client_id].set()

def handle_log(cmd, connect, client_id, server_type):
    latest_log = recv_msg(connect, client_id, server_type)
    if latest_log == '':
        return
    config.latest_log[client_id] = latest_log
    config.action_result[server_type][client_id] = True  
    config.response_ready[server_type][client_id].set()

def handle_remove(cmd,connect,client_id,server_type):
    msg = cmd[0]+' '+cmd[1]+' '+cmd[2]  
    print(msg)

    #rm path file_name   
    if send_msg(msg,connect,client_id,server_type) == False:
        return
    

    ack = recv_msg(connect, client_id, server_type)
    if ack == '':
        return
    
    if ack == 'Path invalid':
        print('Remove: Path invalid.')
        config.error_message[server_type][client_id] = 'path invalid'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    elif ack == 'commit':
        print('Remove: receive commit')
        if server_type == 'maintain':
            #if it's maintain server, no need to gather 2/3 commits
            if send_msg('ACK',connect,client_id,server_type) == False:
                return
            config.action_result[server_type][client_id] = True
    else:
        print('Remove: not receive commit')
        config.action_result[server_type][client_id] = False
            
    config.response_ready[server_type][client_id].set()

def handle_rmdir(cmd,connect,client_id,server_type):
    msg = cmd[0]+' '+cmd[1]  
    print(msg)

    #rm path file_name   
    if send_msg(msg,connect,client_id,server_type) == False:
        return
    

    ack = recv_msg(connect, client_id, server_type)
    if ack == '':
        return
    print('ack in rmdir: '+ack)
    if ack == 'Directory not exists':
        print('Remove_dir: Directory not exists.')
        config.error_message[server_type][client_id] = 'not exist'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    elif ack == 'Directory is not empty':
        print('Remove_dir: Directory not empty.')
        config.error_message[server_type][client_id] = 'not empty'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    elif ack == 'commit':
        print('Rmdir: receive commit')
        if server_type == 'maintain':
            #if it's maintain server, no need to gather 2/3 commits
            if send_msg('ACK',connect,client_id,server_type) == False:
                return
            config.action_result[server_type][client_id] = True
    else:
        print('Rmdir: not receive commit')
        config.action_result[server_type][client_id] = False
            
    config.response_ready[server_type][client_id].set()

def handle_cd(cmd,connect,client_id,server_type):
    msg = cmd[0]+' '+cmd[1] 
    print(msg)
    #cd path
    if send_msg(msg,connect,client_id,server_type) == False:
        return
    

    ack = recv_msg(connect, client_id, server_type)
    print('cd ack: '+ack)
    if ack == '':
        return
    if ack == 'Path invalid':
        print('CD: Path invalid.')
        config.error_message[server_type][client_id] = 'path invalid'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    else:
        config.curr_dir = ack
        config.action_result[server_type][client_id] = True
        config.response_ready[server_type][client_id].set()
        return
        
def handle_mkdir(cmd,connect,client_id,server_type):
    msg = cmd[0]+' '+cmd[1]+' '+cmd[2] 
    print(msg)
    
    if send_msg(msg,connect,client_id,server_type) == False:
        return

    ack = recv_msg(connect, client_id, server_type)
    if ack == '':
        return
    
    if ack == 'Path invalid':
        print('Mkdir: Path invalid.')
        config.error_message[server_type][client_id] = 'path invalid'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    elif ack == 'Directory already exists':
        print('Mkdir: Directory already exists.')
        config.error_message[server_type][client_id] = 'Directory already exists'
        config.action_result[server_type][client_id] = False
        config.response_ready[server_type][client_id].set()
        return
    elif ack == 'commit':
        print('Mkdir: receive commit')
        if server_type == 'maintain':
            #if it's maintain server, no need to gather 2/3 commits
            if send_msg('ACK',connect,client_id,server_type) == False:
                return
            config.action_result[server_type][client_id] = True
    else:
        print('Mkdir: not receive commit')
        config.action_result[server_type][client_id] = False
            
    config.response_ready[server_type][client_id].set()

def receive_file(cmd,connect):
    size = long(cmd[3])
    with open('service_upload/'+cmd[2], 'wb') as f:
        data = recv_msg(connect, -1, 'master')
        if data == '':
            return

        totalRecv = len(data)
        f.write(data)
        while totalRecv < size: 
            print str(totalRecv) + '/' + str(size)
            data = recv_msg(connect, -1, 'master')
            if data == '':
                return
            totalRecv += len(data)
            f.write(data)
        print "Receive Complete!"
    
def send_file(cmd, src_dir, connect):
    src_dir = src_dir + cmd[2] #cmd=[download src_dir filename]
    if os.path.isfile(src_dir):
        filesize = os.path.getsize(src_dir)
    #send filesize to client
    if send_msg(str(filesize),connect,-1,'client') == False:
        return

    with open(src_dir,'rb') as f:
        bytesToSend = f.read(1024)
        if send_msg(bytesToSend,connect,-1,'client') == False:
            return
        while bytesToSend != "":
            bytesToSend = f.read(1024)
            if send_msg(bytesToSend,connect,-1,'client') == False:
                return

    print('Send Complete!')

def send_msg(message, connect, client_id, server_type):
    try:
        connect.send(message)        
    except socket.error, e:
        if isinstance(e.args, tuple):
            print "errno is %d" % e[0]
            if e[0] == errno.EPIPE:
               # remote peer disconnected
                print("pipe broken")
                print("Detected "+"node "+str(client_id)+" disconnect from "+server_type)
            else:
               # determine and handle different error
                print "Detect other error"
        else:
            print("socket error ", e)
            print "Detected "+"node "+str(client_id)+" disconnect from "+server_type
        connect.close()
        if server_type == 'maintain' or server_type == 'service':
            config.STATE_TABLE['maintain'][client_id] = False
            config.STATE_TABLE['service'][client_id] = False
            config.error_message[server_type][client_id] = 'send error'
            config.action_result[server_type][client_id] = False
            config.response_ready[server_type][client_id].set()
        return False
    return True
    
def recv_msg(connect, client_id, server_type):
    try:
        msg = connect.recv(1024)
    except socket.error, e:
        print "Error receiving data: %s" % e
        if server_type == 'maintain' or server_type == 'service':
            config.STATE_TABLE[server_type][client_id] = False
            config.error_message[server_type][client_id] = 'recv error'
            config.action_result[server_type][client_id] = False
            config.response_ready[server_type][client_id].set()
        print('Receive message error: '+'node '+str(client_id)+' may disconnect from '+server_type)
        msg = ''
        return msg

    if not len(msg):
        print('Receive message error: '+'node '+str(client_id)+' may disconnect from '+server_type)
        if server_type == 'maintain' or server_type == 'service':
            config.STATE_TABLE['maintain'][client_id] = False
            config.STATE_TABLE['service'][client_id] = False
            config.error_message[server_type][client_id] = 'recv error'
            config.action_result[server_type][client_id] = False
            config.response_ready[server_type][client_id].set()

    return msg

def two_phase_commit(tc, node_list):        

    if len(node_list) >= 2:
        tc.write_message('ack',node_list)
        tc.wait_response(node_list)
    else:
        tc.write_message('fail', node_list)
        tc.wait_response(node_list)

#retrive log from nodes
def retrive_log(tc, node_list):
    tc.write_message('log',node_list)
    tc.wait_response(node_list)
    #check if returned logs are same
    temp = config.latest_log[node_list[0]]
    same = True
    print('receive log: '+ str(config.latest_log))
    for i in node_list[1:]:
        if temp != config.latest_log[i]:
            same = False
            break;
        temp = config.latest_log[i]

    if same == True:
        mylog = log('master_server.log')
        print('Writing log..')
        mylog.append(config.latest_log[node_list[0]])
    else:
        print('received logs are different.')
            
    

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
