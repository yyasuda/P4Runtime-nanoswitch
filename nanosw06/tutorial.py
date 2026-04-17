#importして使う
from p4runtime_sh.shell import PacketIn, PacketOut, context, client, P4Type, p4runtime_pb2  # 既存クラスを利用
from p4runtime_sh.p4runtime import P4RuntimeWriteException
from google.rpc import code_pb2

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

def insertFlowEntry(dstMac, srcMac, port):
    # context, client は shell 起動後に既に定義されている前提
    req = p4runtime_pb2.WriteRequest()
    update = req.updates.add()
    update.type = p4runtime_pb2.Update.INSERT

    table_entry = update.entity.table_entry
    table_entry.table_id = context.get_obj_id(P4Type.table, "MyIngress.l2_match_table")

    m1 = p4runtime_pb2.FieldMatch()
    m1.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.dstAddr")
    m1.exact.value = dstMac
    m2 = p4runtime_pb2.FieldMatch()
    m2.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.srcAddr")
    m2.exact.value = srcMac
    table_entry.match.extend([m1, m2])

    if port == FLOOD_PORT: # set action to flooding 
        print("  ## set flooding action")
        action = table_entry.action.action
        action.action_id = context.get_obj_id(P4Type.action, "MyIngress.flooding") # 16838673 
    else:                  # set action to forward to the port 
        action = table_entry.action.action
        action.action_id = context.get_obj_id(P4Type.action, "MyIngress.forward") # 16838673 
        param = p4runtime_pb2.Action.Param()    
        param.param_id = context.get_param_id("MyIngress.forward", "port") # 1
        param.value = port 
        action.params.append(param)

    try:
        client.write(req)
    except P4RuntimeWriteException as e:
            if e.errors[0][1].canonical_code == code_pb2.ALREADY_EXISTS:
                print("Flow already exists. ignoring.")
            else:
                print(e)
                raise e

def my_packetin(pin):
    global macTable
    payload = pin.packet.payload
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = pin.packet.metadata[0].value

    print("\npacket-in: dst={0} src={1} port={2}"
          .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port,'big')))

    if dstMac == b'\xff\xff\xff\xff\xff\xff':  # broadcast
        if srcMac not in macTable:
            macTable[srcMac] = port
        insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
        my_packetout(str(int.from_bytes(port,'big')), FLOOD_GRP, payload)
    else:  # unicast
        if srcMac not in macTable:
            macTable[srcMac] = port
        if dstMac in macTable:
            insertFlowEntry(dstMac, srcMac, macTable[dstMac])
            insertFlowEntry(srcMac, dstMac, macTable[srcMac])
            out_port = str(int.from_bytes(macTable[dstMac],'big'))
            mcast_grp = '0x0000'
        else:
            out_port = str(int.from_bytes(port,'big'))
            mcast_grp = FLOOD_GRP
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
