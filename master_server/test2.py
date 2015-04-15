

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
        
def main():
    mylog = log('master_server.log')
    print mylog.get_latest_index()

if __name__ == '__main__':
    main()
