#importして使う
from p4runtime_sh.shell import PacketIn, PacketOut, context, client, P4Type, p4runtime_pb2  # 既存クラスを利用

FLOOD_GRP = '0x0001'
FLOOD_PORT = b'\xff\xff'
macTable = {}

def mac2str(mac):
    return ':'.join('{:02x}'.format(b) for b in mac)

def my_packetout(port, mcast_grp, payload):
    packet = PacketOut(payload)
    packet.metadata['egress_port'] = port
    packet.metadata['mcast_grp'] = mcast_grp
    packet.send()
    print('send \n', packet)

def my_packetin(pin):
    global macTable
    payload = pin.packet.payload #パケットのボディ
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = pin.packet.metadata[0].value #ingress_port Switchではこのportへegress処理されるパケットはdropされる

    print("\npacket-in: dst={0} src={1} port={2}"
          .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port,'big')))
    
    mcast_grp = '0x0001'
    out_port = str(int.from_bytes(port,'big'))
    my_packetout(out_port, mcast_grp, payload)
    
    

def controller_daemon(packet_in, my_packetin=None, args=None):
    if my_packetin is None:
        while True:
            try:
                print(packet_in.packet_in_queue.get(block=True))
            except KeyboardInterrupt:
                break
    else:
        while True:
            try:
                pin = packet_in.packet_in_queue.get(block=True)
                my_packetin(pin)
            except KeyboardInterrupt:
                break
