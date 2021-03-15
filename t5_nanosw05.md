## Tutorial 5: NanoSwitch05

By the way, until now we did not have any treatment of the ARP packet. All broadcast packets were ignored. Here, when the broadcast arrives, we add it to the flow entry to prevent it from coming to the controller anymore.

### Experiment

#### Mininet operation

Exit Mininet once then restart it without --arp option. It allows sending ARP in the initial stage.

```bash
mininet> exit
*** Stopping 0 controllers
(snip...)
*** Done
completed in 1063.313 seconds
$

$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

#### P4Runtime Shell operation

Terminate the execution of the P4Runtime Shell and replace shell.py with the expanded version of it in nanosw05 directory.

```python
P4Runtime sh >>> exit
(venv) root@1923f14d3a08:/tmp/nanosw03# cd ../nanosw05
(venv) root@1923f14d3a08:/tmp/nanosw05# cp shell.py /p4runtime-sh/p4runtime_sh/shell.py 
(venv) root@1923f14d3a08:/tmp/nanosw05# cp context.py /p4runtime-sh/p4runtime_sh/context.py 
(venv) root@1923f14d3a08:/tmp/nanosw05# 
```

Since the switch program has a modification this time, execute nanosw05 and call the PacketIn() function.

```python
(venv) root@f4f19294589c:/tmp/nanosw05# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw04.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> PacketIn()

......
```

#### Again, Mininet operation

If you send ping requests again here, you can confirm that the ping responses are returned correctly.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.98 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 8.986/8.986/8.986/0.000 ms
mininet>
```
#### P4 RuntimeShell operation

At this time, you can see the following messages. Up to the first two packets are Packet-In back to the controller. After the flow entry is set in the second Packet-In process, it is no longer Packet-In to the controller.
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
```
#### PrintTable()

We made a PrintTable() function to check the flow entry registered in the l2_match_table. Will the contents of the flow entries are displayed in the following manner. At this timing, three entries should be registered in the table. The first is for flooding the broadcast, and the other two are entries for forwarding packet round trips between h1 and h2.

```bash
P4Runtime sh >>> PrintTable("MyIngress.l2_match_table")                                                                                         
MyIngress.l2_match_table
  dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 action=MyIngress.flooding
  dst=00:00:00:00:00:01 src=00:00:00:00:00:02 action=MyIngress.forward ( 1 )
  dst=00:00:00:00:00:02 src=00:00:00:00:00:01 action=MyIngress.forward ( 2 )

P4Runtime sh >>>     

<<<< It is good idea to delete entires as follows, to see this behavior again.
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: a.delete())                                                                                                          

```

### Packet round trip and flow table hadling

The following is a more detailed explanation of the round trip of packets and internal processing.

1. ARP request comes out from h1
2. The switch do packet-in to the controller
3. The controller registers to flow entry, with the destination is broadcast and source is h1 and action is flooding. 
4. The controller floods the received packet (packet-out other than the received port)
5. h2 receives the ARP packet forwarded by 4. and sends a reply to it.
6. Again, this pattern is not in the flow entry, so packet-in to the controller
7. The controller registers the pattern of destination h1 and source h2 as action forward.
8. The controller floods the received packet (packet-out other than the received port)

All subsequent communication between h1 and h2 is forwarded only by the switch, not through the controller. No Packet-In or flooding will occur.



### Related codes

We've made some modifications to achieve this. I will explain along the packet flow.

#### nanosw05.p4

As the action in the l2_match_table table, re-enable flooding, which hasn't been used for some time. However, be aware that in action flooding(), you set the multicast group to 1 and store the ingress port number in meta.ingress_port.

```C++
    action flooding() {
        // hardcoded, you must configure multicast-group 1 at runtime
        standard_metadata.mcast_grp = 1;
        meta.ingress_port = standard_metadata.ingress_port; // store exection port
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

#### shell.py

The process of "action flooding" setting is implemented in some functions in shell.py that you replaced earlier. Shows an excerpt only major parts below. First, related to the PacketIn() function.

```Python
FLOOD_PORT = b'\xff\xff'
def packetin_process(pin):
    payload = pin.packet.payload
    port = pin.packet.metadata[0].value   # original ingres_port
    payload = pin.packet.payload
    if dstMac == b'\xff\xff\xff\xff\xff\xff':
        print("broadcast!")
        if srcMac not in macTable:
            macTable[ srcMac ] = port
        insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
        PacketOut(port, FLOOD_GRP, payload)
    else: # when destination is unicast, do forwarding
        # if the source is new, record it with ingress port
        if srcMac not in macTable:
            macTable[ srcMac ] = port
        if dstMac in macTable: # if the destination is recorderd, set entry
            insertFlowEntry(dstMac, srcMac, macTable[ dstMac ])
            insertFlowEntry(srcMac, dstMac, macTable[ srcMac ])
            # send to appropriate port
            port = macTable[ dstMac ]
            mcast_grp = b'\x00\x00' # no Multicast
        else:
            # send to all (except original ingress port)
            mcast_grp = FLOOD_GRP 
        # Packet-out (as single-out or flood) 
        PacketOut(port, mcast_grp, payload)

def insertFlowEntry(dstMac, srcMac, port):
    (...snip...)
    if port is FLOOD_PORT: # set action to flooding 
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

```

That is, the packetin_process() function calls insertFlowEntry() with the port number as FLOOD_PORT (which marks the process to be flooded) if the received packet is a broadcast. If where a port number is FLOOD_PORT, sets the flow entry with the flooding as action. If it is not broadcast, the port number will be the ingress port, and in insertFlowEntry(), set the flow entry with forward as action.

If the port where the destination host exists is known, specify Unicast and call the PacketOut () function with the information of that port. If this is not the case, that is, if the broadcast or destination host port is unknown, call the PacketOut () function with the Multicast Group information (1) and the original Ingress_port information.

#### Ping processing time before and after entry setting

Now again sending a ping request, you can see that come back is just as well ping response. However, this time the packet wraps according to the flow entry configured on the switch and is never sent to the controller.

Notice its response time. So this time the host on the Mininet will not issue her ARP packets. There is no flow entry setting on the controller side or transfer processing by Packet Out. You can see that the process is processed in short time, inside the switch. In my environment, the first time takes about 9ms, but after that he completes in less than 1ms.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.783 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.783/0.783/0.783/0.000 ms
mininet> 
```



You have completed the series of tutorials. Congratulations!

## Next Step

Is [this](README.md#next-step) good for the next?

