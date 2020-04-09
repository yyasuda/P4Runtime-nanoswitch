## Tutorial 4: NanoSwitch04

Create a host table on the controller side to correspond to known hosts. This means adding round-trip entries to the flow table for communications between known host pairs. After that, switch forwards the round-trip packet without going through the controller.

###  For those who start from here to shortcut

This experiment requires the following process:

1. Start the P4 Runtime Shell and Connect to Mininet - see; Tutorial 0: [Preparation the Environment](./t0_prepare.md)
2. Multicast Group Settings - see; Tutorial 1: [NanoSwitch01](./t1_nanosw01.md)
Without it, Flooding will not happen. And since there are no (visible) errors, you won't know why it doesn't work.

### Experiment

#### P4Runtime Shell operation

Terminate the execution of the P4Runtime Shell and replace shell.py with the expanded version of it in nanosw04 directory. 

```python
P4Runtime sh >>> exit
(venv) root@1923f14d3a08:/tmp/nanosw03# cd ../nanosw04
(venv) root@1923f14d3a08:/tmp/nanosw04# cp shell.py /p4runtime-sh/p4runtime_sh/shell.py 
(venv) root@1923f14d3a08:/tmp/nanosw04# cp context.py /p4runtime-sh/p4runtime_sh/context.py 
(venv) root@1923f14d3a08:/tmp/nanosw04# 
```

Since there is no change in the switch program this time, execute nanosw03 again and call the PacketIn() function.

```python
(venv) root@f4f19294589c:/tmp/nanosw04# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw03.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> PacketIn()

......
```

#### Mininet operation

If you send ping requests again here, you can confirm that the ping responses are returned correctly.

```bash
mininet> h1 ping h2        <<<<<< ping from h1 to h2 repeatedly
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.38 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.701 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.778 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=1.13 ms
^C
--- 10.0.0.2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3055ms
rtt min/avg/max/mdev = 0.535/0.772/1.114/0.221 ms
mininet> 
```
#### P4 RuntimeShell operation
At this time, you can see the following messages. Up to the first two packets are returned to the controller by Packet-In, and since flow entries are set by the second Packet-In processing, it is no longer packet-In to the controller.
```bash
P4Runtime sh >>> PacketIn()

........
======              <<<< 1st packet processing
packet-in: dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=1
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
.
======              <<<< 2nd packet processing
packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2
## INSERT ## dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=1
## INSERT ## dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=2
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:02 - port(2)
. 　　　　　
......^C  <<<< Subsequent ping packets are not Packet-In (interrupted by Control-C)
Nothing (returned None)

P4Runtime sh >>> 

<<<< You can check the flow entries registered in l2_match_table as follows
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01"
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x02"
  }
}
action {
  action {
    action_id: 16838673 ("MyIngress.forward")
    params {
      param_id: 1 ("port")
      value: "\\x00\\x01"
    }
  }
}

table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x02"
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01"
  }
}
action {
  action {
    action_id: 16838673 ("MyIngress.forward")
    params {
      param_id: 1 ("port")
      value: "\\x00\\x02"
    }
  }
}

P4Runtime sh >>>
```
### Packet round trip and flow table contents

The following is a more detailed explanation of the round trip of packets and internal processing.

To realize this processing, the controller maintains a table (Variable Name macTable) of host MAC addresses and port numbers to which they are connected. This is called the host table. Let's call the table on the switch side, l2_match_table, the flow table.

First, I'll illustrate the step-by-step state of the two tables.

<img src="experiment.png" alt="attach:(Packet and flow entry sequences)" title="Packet and flow entry sequences">
The details are described below.

#### 1. Initial State

Initially, both the host table and flow table are empty.
```python
macTable = {}
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
|         |         |      |

#### 2. h1 -> h2 : ICMP Echo Request

The first packet does not match the flow table match patterns and process as Packet-In. Controller that has received this, do the following processing.
1. The address of the source MAC of h1 is not in the host table. It is "Unknown" and recorded in the host table along with the ingress port, port1.
2. There is nothing we can do because the address of the destination h2 is also "Unknown".
3. The packet will be processed as Packet-Out with a Flooding designation.
```python
macTable = { "00:00:00:00:00:01": 1 }
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
|         |         |      |

#### 3. h2 -> h1 : ICMP Echo reply

Echo Request is to reach the h2 by Flooding, h2 will send a reply for h1. However, the packet does not match the flow table match patterns and process as Packet-In. Controller that has received this, do the following processing.

1. The address of the source MAC of h2 is not in the host table. It is "Unknown" and recorded in the host table along with the ingress port, port2.
3. It is clear that the destination h1 is already existing in the host table and can be sent to port 1. Now that you have the destination and source information, add the round-trip entries to the flow table.
4. The packet will be processed as Packet-Out to port 1.

```python
macTable = { "00:00:00:00:00:01": 1,
             "00:00:00:00:00:02": 2 }
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
| 00:00:00:00:00:01 | 00:00:00:00:00:02 | 1 |
| 00:00:00:00:00:02 | 00:00:00:00:00:01 | 2 |

#### 4. after that....

All subsequent communication between h1 and h2 is forwarded only by the switch, not through the controller. No Packet-In or flooding will occur.



### Related codes

This time, we use the same nanosw03.p4 switch program as in Tutorial 3. The only difference from Tutorial 3 is the controller side, that is, shell.py and context.py.

#### shell.py

Here is the packetin_process () function that plays the most important role in this version. The packet round trip between h1 and h2 and the corresponding internal processing described above have been implemented.

```python
def packetin_process(pin):
    payload = pin.packet.payload
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = metadata_value(pin.packet.metadata, "packet_in", "ingress_port") # original ingres_port
    print("\n======\npacket-in: dst={0} src={1} port={2}"
            .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port, byteorder='big')))

    # if the source is new, record it with ingress port
    if srcMac not in macTable:
        macTable[ srcMac ] = port
    # when destnation is broadcast, no need to record it
    if dstMac == b'\xff\xff\xff\xff\xff\xff':
        print("broadcast!")
    else:
        if dstMac in macTable: # if the destination is recorderd, set entry
            insertFlowEntry(dstMac, srcMac, macTable[ dstMac ])
            insertFlowEntry(srcMac, dstMac, macTable[ srcMac ])
            # send to appropriate port
            port = macTable[ dstMac ]
            mcast_grp = b'\x00' # no Multicast
        else:
            # send to all (except original ingress port)
            mcast_grp = FLOOD_GRP 
        # Packet-out (as single-out or flood) 
        PacketOut(port, mcast_grp, payload)

```

The insertFlowEntry() function called from the packetin_process() function above is also in shell.py.

```python
def insertFlowEntry(dstMac, srcMac, port):
    print("## INSERT ## dst={0} src={1} port={2}" 
            .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port, byteorder='big')))

    req = p4runtime_pb2.WriteRequest()
    update = req.updates.add()
    update.type = p4runtime_pb2.Update.INSERT

    table_entry = update.entity.table_entry
    table_entry.table_id = context.get_obj_id(P4Type.table, "MyIngress.l2_match_table") # 33609159 
    m1 = p4runtime_pb2.FieldMatch()
    m1.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.dstAddr") # 1 
    m1.exact.value = dstMac
    m2 = p4runtime_pb2.FieldMatch()
    m2.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.srcAddr") # 2
    m2.exact.value = srcMac
    table_entry.match.append(m1)
    table_entry.match.append(m2)

    action = table_entry.action.action
    action.action_id = context.get_obj_id(P4Type.action, "MyIngress.forward") # 16838673 
    param = p4runtime_pb2.Action.Param()    
    param.param_id = context.get_param_id("MyIngress.forward", "port") # 1
    param.value = port 
    action.params.append(param)

    client.write(req)
```



#### context.py

By the way, until Tutorial 3, P4 Entity to be given to the message of P4Runtime was directly specified by id number. This tutorial uses the context.get_obj_id() and context.get_mf_id() functions to get the id number of a table or field by the name. These functions are defined in context.py.

Also, there were no functions implemented for handling controller packet metadata, so I added them to context.py. It is used by the metadata_value() function, which is called by the packetin_process() function.



You have completed the series of tutorials. Congratulations!

## Next Step

Is [this](README.md#next-step) good for the next?

