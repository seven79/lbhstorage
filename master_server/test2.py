

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
        
def main():
    mylog = log('master_server.log')
    print mylog.read_line(5)

if __name__ == '__main__':
    main()
