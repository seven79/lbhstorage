import threading

ms1 = threading.Event()
ms2 = threading.Event()
ms3 = threading.Event()
mm1 = threading.Event()
mm2 = threading.Event()
mm3 = threading.Event()

rs1 = threading.Event()
rs2 = threading.Event()
rs3 = threading.Event()
rm1 = threading.Event()
rm2 = threading.Event()
rm3 = threading.Event()

STATE_TABLE ={'service':[False, False, False], 
              'maintain':[False, False, False],
              }

#Global variabel used to realize communication between threads
message = {'maintain':['','',''],
           'service':['','',''],
       }

message_ready = {'maintain':[mm1, mm2, mm3],
                 'service': [ms1, ms2, ms3],
             }
response_ready = {'maintain':[rm1, rm2, rm3],
                  'service': [rs1, rs2, rs3],
              }
handler_exist ={'service':[False, False, False], 
              'maintain':[False, False, False],
              } 
action_result = {'maintain':[False, False, False],
                  'service': [False, False, False],
              }
error_message = {'maintain':['','',''],
                 'service':['','',''],
             }
latest_index = [-1, -1, -1]

latest_log =['','','']

curr_dir = ''


if __name__ == '__main__':
    test()
