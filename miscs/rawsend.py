import socket
iface = 's1-eth1'
dstMac = b'\x01\x01\x01\x01\x01\x01'
srcMac = b'\x02\x02\x02\x02\x02\x02'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
s.send(packet)
print('Packet sent.')
s.close()
