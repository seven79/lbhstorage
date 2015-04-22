import threading

e1 = threading.Event()


def test(b):
    b[0] = [1,2]

    
if __name__ == '__main__':
    a = [2,3,4]
    b = [a]
    test(b)
    print b[0]
