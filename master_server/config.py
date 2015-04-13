

STATE_TABLE ={'service':[False, False, False], 
              'maintain':[False, False, False],
              }

#Global variabel used to realize communication between threads
message = {'maintain':['','',''],
           'service':['','',''],
       }

message_ready = {'maintain':[False, False, False],
                 'service': [False, False, False],
             }
response_ready = {'maintain':[False, False, False],
                  'service': [False, False, False],
              }
action_result = {'maintain':[False, False, False],
                  'service': [False, False, False],
              }
latest_index = [-1, -1, -1]
