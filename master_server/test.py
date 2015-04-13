#import master_server
#import threading
#import config
#import service


def a():
    print('I am a')

def b():
    print('I am b')

def c():
    print('I am c')

test_switch = {'a':a,
               'b':b,
               'c':c
           }

'''def master_server_test():
    service_server = master_server.server('service', '127.0.0.1', 8001)
    maintain_server = master_server.server('maintain', '127.0.0.1', 8002)
    t1 = threading.Thread(target=service_server.start, args=())
    t2 = threading.Thread(target=maintain_server.start, args=())
    t1.start()
    t2.start()'''

if __name__ == '__main__':
    #master_server_test()
    test_switch.get('c')()
    test_switch.get('a')()
    test_switch.get('b')()

