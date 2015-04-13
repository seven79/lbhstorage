
class dir:
    def __init__(self,user):
        self.user = user
        self.curr = ''

    #open a directory, return file list in this directory
    def cd_dir(self, sub_dir):
        if sub_dir == '..':
            if self.curr != '':
             self.curr = self.curr[:self.curr.find('/',1)]
        elif sub_dir != '.':
            self.curr += '/' + sub_dir
        print(self.curr)

    #query available node to get filelist in current directory
    def get_filelist(self):
        #check how many nodes are available 
        #choose one and query it with current directory

#def service(connect):
    


if __name__ == '__main__':
    d1 = dir('simon')
    print(d1.user)
    d1.cd_dir('Documents/project')
    d1.cd_dir('..')
    d1.cd_dir('.')
