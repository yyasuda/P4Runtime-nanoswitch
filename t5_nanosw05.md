## Tutorial 5: NanoSwitch05

Up to this point, ARP packet processing has not been handled. In other words, broadcast packets were ignored. Here, when a broadcast is received, it is added to the flow entry so that it will no longer be sent to the controller afterward.

### Experiment

#### Operations on the Mininet side

Exit Mininet and restart it without the --arp option. This causes ARP packets to be sent first.

```bash
mininet> exit
*** Stopping 0 controllers
(snip...)
*** Done
completed in 1063.313 seconds
$

$ docker run --privileged --rm -it -p 50001:50001 -e IPV6=false yutakayasuda/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

#### Operations on the P4Runtime Shell side

First, exit the P4Runtime Shell, and restart it using the nanosw05 switch program under nanosw05.

```python
P4Runtime sh >>> exit
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw05/p4info.txt,/tmp/nanosw05/nanosw05.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```

Since Mininet was restarted, do not skip reconfiguring the Multicast Group.

```python
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>>
```

After that, start the controller program tutorial.py located under /tmp/nanosw05 as follows.

```python
P4Runtime sh >>> import sys

P4Runtime sh >>> sys.path.append "/tmp/nanosw05"

P4Runtime sh >>> import tutorial

P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```

#### Operations on the Mininet side again

When you send a ping request again here, you can confirm that a correct ping reply is returned.

```bash
mininet> h1 ping h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=2.33 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.866 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.919 ms
^C
--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2013ms
rtt min/avg/max/mdev = 0.866/1.372/2.331/0.678 ms
mininet> 
```

At this time, if you monitor the Mininet ports, you can confirm that not only ICMP packets but also ARP packets are exchanged.

```bash
00:58:51.242280 ARP, Request who-has 10.0.0.1 tell 10.0.0.2, length 28
00:58:51.242330 ARP, Reply 10.0.0.1 is-at 00:00:00:00:00:01 (oui Ethernet), length 28
00:59:57.322896 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 1, length 64
00:59:57.325070 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 1, length 64
00:59:58.325092 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 2, length 64
00:59:58.325904 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 2, length 64
00:59:59.335442 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 3, length 64
00:59:59.336214 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 3, length 64
```

#### P4 RuntimeShell screen

At the same time, you can confirm that output like the following is displayed on the P4Runtime Shell side. The first ARP request packet is returned to the controller via Packet-In and sent as Packet-Out with multicast specified for flooding. The second ARP response packet is processed as Packet-In and sent as Packet-Out to port 1. In parallel, three flow entries are set: broadcast, h1 -> h2, and h2 -> h1. After that, no more Packet-In processing occurs.

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action
send 
 payload: "\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x01\x08\x06\x00\x01\x08\x00\x06\x04\x00\x01\x00\x00\x00\x00\x00\x01\x0a\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0a\x00\x00\x02"
metadata {
  metadata_id: 1 ("egress_port")
  value: "\x00\x01"
}
metadata {
  metadata_id: 2 ("_pad")
  value: "\x00"
}
metadata {
  metadata_id: 3 ("mcast_grp")
  value: "\x00\x01"
}


packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2
send 
 payload: "\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x02\x08\x06\x00\x01\x08\x00\x06\x04\x00\x02\x00\x00\x00\x00\x00\x02\x0a\x00\x00\x02\x00\x00\x00\x00\x00\x01\x0a\x00\x00\x01"
metadata {
  metadata_id: 1 ("egress_port")
  value: "\x00\x01"
}
metadata {
  metadata_id: 2 ("_pad")
  value: "\x00"
}
metadata {
  metadata_id: 3 ("mcast_grp")
  value: "\x00\x00"
}

^C  <<<< subsequent ping packets are not processed as Packet-In (interrupt with Control-C)
P4Runtime sh >>> 

<<<< You can also check the flow entries registered in l2_match_table as follows.
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
...(snip)
```

#### Table contents

You can check the flow entries registered in l2_match_table as follows. The first entry is for flooding broadcast packets, and the remaining two are for forwarding packets between h1 and h2.

```bash
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< entry for flooding broadcast
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\xff\xff\xff\xff\xff\xff"  <<<< destination is "ff:ff:ff:ff:ff:ff"
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\x01"
  }
}
action {
  action {
    action_id: 16837454 ("MyIngress.flooding")  <<<< call flooding function
  }
}

table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< entry for h2 -> h1
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\x01"
  }
}
...(snip)

table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< entry for h1 -> h2
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\x02"
  }
}
...(snip)

<<<< It is a good idea to delete the table contents as follows and observe the behavior again.
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: a.delete())

```

### Packet exchanges and flow table operations

Below, we explain the packet exchanges and internal processing that occur when h1 pings h2.

1. h1 sends an ARP request
2. The switch sends it to the controller as Packet-In
3. The controller registers a flow entry with destination broadcast, source h1, and action flooding
4. The controller floods the received packet (Packet-Out to all ports except the receiving port)
5. h2 receives the ARP packet forwarded in step 4 and sends a reply
6. This pattern is also not in the flow table, so it is sent to the controller as Packet-In
7. The controller registers the pattern with destination h1 and source h2 as action forward
8. The controller floods the received packet (Packet-Out to all ports except the receiving port)

After this, all communication between h1 and h2 is forwarded by the switch alone without involving the controller. No Packet-In or flooding occurs.

### Related code

To realize this behavior, several modifications have been made. They are explained following the packet flow.

#### nanosw05.p4

Enable the flooding action again in l2_match_table, which had not been used for a while. Note that in the flooding() action, multicast group 1 is set and the input port number is stored in meta.ingress_port.

```C++
    action flooding() {
        // hardcoded, you must configure multicast-group 1 at runtime
        standard_metadata.mcast_grp = 1;
        meta.ingress_port = standard_metadata.ingress_port; // store exception port
    }
    table l2_match_table {
        key = {
            hdr.ethernet.dstAddr: exact;
            hdr.ethernet.srcAddr: exact;
        }
        actions = {
            forward;
            to_controller;
            flooding;
        }
        size = 1024;
        default_action = to_controller;
    }
```

#### tutorial.py

The processing that sets this flooding action is implemented in several functions in the replaced shell.py. The main parts are shown below. First, the PacketIn() related function.

```Python
FLOOD_GRP = '0x0001'
FLOOD_PORT = b'\xff\xff'
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

def insertFlowEntry(dstMac, srcMac, port):
    (...snip...)
    if port == FLOOD_PORT: # set action to flooding 
        print("  ## set flooding action")
        action = table_entry.action.action
        action.action_id = context.get_obj_id(P4Type.action, "MyIngress.flooding") 
    else:                  # set action to forward to the port 
        action = table_entry.action.action
        action.action_id = context.get_obj_id(P4Type.action, "MyIngress.forward") 
        param = p4runtime_pb2.Action.Param()    
        param.param_id = context.get_param_id("MyIngress.forward", "port") 
        param.value = port 
        action.params.append(param)
```

In other words, if the received packet is broadcast, the my_packetin() function calls insertFlowEntry() with the port number set to FLOOD_PORT (a marker for flooding). In insertFlowEntry(), if the port number is FLOOD_PORT, the flooding action is set in the flow entry. If it is not broadcast, the port number is the input port, and the forward action is set in insertFlowEntry().

If the port of the destination host is known, PacketOut() is called with unicast specification and the corresponding port information. Otherwise, that is, for broadcast or when the destination host port is unknown, PacketOut() is called with Multicast Group information (1) and the original ingress_port information.

#### Ping processing time before and after entry setup

When you send a ping request again here, you can confirm that a ping reply is returned as before. However, this time the packets are handled according to the flow entries set in the switch and are not sent to the controller.

Pay attention to the response time. This time, hosts on Mininet do not send ARP packets. There is also no flow entry setup or Packet-Out forwarding on the controller side. You can confirm that processing is completed quickly by the switch alone. In my environment, the first time takes about 3–5 ms, while subsequent responses complete in less than 1 ms.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.783 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.783/0.783/0.783/0.000 ms
mininet> 
```



## Next Step

#### Tutorial 5: [NanoSwitch06](t6_nanosw06.md)
