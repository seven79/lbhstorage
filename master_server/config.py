

STATE_TABLE ={'service':[False, False, False], 
              'maintain':[False, False, False],
              }

#Global variabel used to realize communication between threads
maintain_message = ['','','']
messsage_ready = [False, False, False]
response_ready = [False, False, False]
latest_index = [-1, -1, -1]
action_result = [False, False, False]
