import master_server

def client_test():
    client1 = master_server.client('127.0.0.1', 8001, 0)
    client1.start()
    client2 = master_server.client('127.0.0.1', 8001, 1)
    client2.start()
    client3 = master_server.client('127.0.0.1', 8001, 2)
    client3.start()
    client4 = master_server.client('127.0.0.1', 8002, 0)
    client4.start()
    client5 = master_server.client('127.0.0.1', 8002, 1)
    client5.start()
    client6 = master_server.client('127.0.0.1', 8002, 2)
    client6.start()

if __name__ == '__main__':
    client_test()
