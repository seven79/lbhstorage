
class dir:
    def __init__(self,user):
        self.user = user
        self.curr = ''

#open a directory, return file list in this directory
    def cd_dir(self, sub_dir):
        if sub_dir == '..':
            self.curr 
        self.curr += '/' + sub_dir
        print(self.curr)
          get_list(self.curr)


    def get_list(curr_dir):
        


d1 = dir('simon')
print(d1.user)
d1.cd_dir('Documents')
