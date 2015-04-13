'''TABLE = [True, False, True]
latest_index = [3,3,4]
node_list=[]
valid_list=[]
invalid_list=[]
#check if connected clients >= 2
while len(node_list) < 2:
    del node_list[:]
    for i in range(3):
        if TABLE[i] == True:
            node_list.append(i)
print node_list
#check which node need to recovery by compare latest index 
for i in node_list:
    if latest_index[i] == 4:
        valid_list.append(i)
    else: 
        invalid_list.append(i)

print valid_list
print invalid_list'''

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
        log = ''
        with open(self.filename) as f:
           log = f.readlines()[line-1]
        return log

mylog = log('master_server.log')
mylog.append('6 upload /adfas/adfads/adf.r /adfas/asdf/asdf/')
msg = mylog.read_line(2)
msg = msg.strip('\n')
print msg
