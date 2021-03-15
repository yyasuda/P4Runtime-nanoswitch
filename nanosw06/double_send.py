import socket
import time
iface = 'h1-eth0'
dstMac = b'\xff\xff\xff\xff\xff\xff'
srcMac = b'\x00\x00\x00\x00\x00\x01'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
print('send #1 packet.')
s.send(packet)
time.sleep(1)
print('send #2 packet.')
s.send(packet)
print('done.')
s.close()
