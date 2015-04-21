import threading

e1 = threading.Event()


def test(a):
    a[0] = 1

    
if __name__ == '__main__':
    a = [2,3,4]
    test(a)
    print a
