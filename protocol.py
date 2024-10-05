'''
@author: hao
'''

#defines the protocol header
HEAD_REQUEST='REQ'
HEAD_DISCONNECT = 'DIS'
HEAD_CONN = 'CON'
HEAD_ERROR='ERR'

# we prepare the message that are sent between server and client as the header + content
def prepareMsg(header, msg):
    return (header+msg).encode()

# Decode the received message, the first three letters are used as protocol header
def decodeMsg(msg):
    if (len(msg)<=3):
        return HEAD_ERROR, 'EMPTY MESSAGE'
    else:
        return msg[0:3],msg[3:len(msg)]