## Tutorial 3: NanoSwitch03

This time, the switch creates a flow table on the switch side to accommodate the unknown host. We will add some functionality to the controller (P4Runtime Shell) for the process of registering entries into the flow table.

### Experiment

#### P4Runtime Shell operation

Terminate the execution of the P4Runtime Shell and replace shell.py with the expanded version of it in nanosw03 directory. 

```python
P4Runtime sh >>> exit
(venv) root@f4f19294589c:/tmp/nanosw02# cd ../nanosw03
(venv) root@f4f19294589c:/tmp/nanosw03# cp shell.py /p4runtime-sh/p4runtime_sh/shell.py 
(venv) root@f4f19294589c:/tmp/nanosw03# 
```

Re-run the switch with the new switch program nanosw03, then call the PacketIn() function.
```python
(venv) root@f4f19294589c:/tmp/nanosw03# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw03.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> PacketIn()

......
```
#### Packets you don't know

You might see the following packets displaying;
```bash
======
packet-in: dst=33:33:00:00:00:02 src=00:00:00:00:00:03 port=3
macTable (mac - port)
 00:00:00:00:00:03 - port(3)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
.....
```
33:33:00:00:00:02 is the Multicast MAC address that IPv6 uses for processing Router Solicitation or some. Let us just ignore them in this tutorial.

#### Mininet operation

If you send a ping request again here, you can confirm that the ping response is returned as before.
```bash
mininet> h1 ping -c 1 h2       <<<<<< ping from h1 to h2 once
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=6.23 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 6.233/6.233/6.233/0.000 ms
mininet> 

```

The monitoring results of each port are shown below. You can see that this also suppresses unnecessary packet repeating.

#####  h1 (s1-eth1)

```bash
12:30:55.734450 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.740638 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

##### h2 (s1-eth2)

```bash
12:30:55.738186 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.738210 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

##### h3 (s1-eth3)

```bash
12:30:55.738150 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.740679 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

#### P4 RuntimeShell operation

At this time, you can see the following messages. You can see that both of the two packets that have been round tripped are processed in Packet-In.

```bash
P4Runtime sh >>> PacketIn()
........
======              <<<< 1st packet processing
packet-in: dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=b'\x00\x01'
.
======              <<<< 2nd packet processing
packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=b'\x00\x02'
..
......^C  <<<< interrupted by Control-C 
```

The following sections describe the behavior of the packet in this experiment.

### The behavior of the packet

#### A sketch

This switch floods all received packets to other ports through the controller. The figure below shows that packets sent by host 1 are sent to host 2 and host 3 via the controller.

<img src="packet_path.png" alt="attach:(packet path)" title="Packet Path" width="300">

This section describes in some detail.

1. The packet issued by host 1 is output as Packet-In to the controller
2. The controller sets this to MulticastGroup id 1 and performs Packet-Out
3. Switch receives this from CPU_PORT, duplicates as Multicast, and outputs
4. However, packets that are output to the same port as the original input port (port 1) are dropped

We made some modifications to nanosw03.p4 to achieve this. The explanation follows the flow of the packet.

#### Processing associated with Packet-In

The default_action in the l2_match_table table is to_controller and the flow table is currently empty, so all packets will be packet-in to the controller. Here flooding action is not used.

```C++
    action to_controller() {
        standard_metadata.egress_spec = CPU_PORT;
        hdr.packet_in.setValid();
        hdr.packet_in.ingress_port = standard_metadata.ingress_port;
    }
    table l2_match_table {
        key = {
            hdr.ethernet.dstAddr: exact;
            hdr.ethernet.srcAddr: exact;
        }
        actions = {
            forward;
            to_controller;
            // flooding;
        }
        size = 1024;
        default_action = to_controller;
    }
```
This Packet-In processing is implemented in the shell.py replaced earlier.
```Python
def packetin_process(pin):
    payload = pin.packet.payload
    port = pin.packet.metadata[0].value   # original ingres_port
    mcast_grp = b'\x00\x01'   # caution, hardcoded multicast group
    payload = pin.packet.payload
    PacketOut(port, mcast_grp, payload)
    
def PacketIn():
        while True:
            rep = client.get_stream_packet("packet", timeout=1)
            if rep is not None:
                packetin_process(rep)
```

The PacketIn () function waits for the StreamMessage Response, and upon receiving it, gives the received Packet-In packet as an argument and calls the packetin_process () function. The packet_process() function always passes the received packet to the PacketOut() function with the Multicast Group id (1) and the original Ingress_port information.

#### Processing associated with Packet-Out

The implementation of packet_out header and PacketOut() function is shown below. Multicast Group information is added to the packet_out header.

```C++
@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port;
    bit<7> _pad;
    bit<16> mcast_grp; 
}
```

```python
def PacketOut(port, mcast_grp, payload):
    req = p4runtime_pb2.StreamMessageRequest()
    packet = req.packet
    packet.payload = payload

    metadata = p4runtime_pb2.PacketMetadata()
    metadata.metadata_id = 1   <<<<< egress_port
    metadata.value = port
    packet.metadata.append(metadata)
    metadata.metadata_id = 3   <<<<< mcast_id
    metadata.value = mcast_grp
    packet.metadata.append(metadata)

    client.stream_out_q.put(req)
```

The PacketOut() function is very simple: it sets a packet_out header and sends it to the switch. 

#### Ingress processing on the received switch side

The packet-out processing on nanosw03.p4 had been modified to respond mcat_grp field of this expanded packet_out header.
It was originally written as follows. That is, if it is a Packet-Out (Packets from CPU_PORT), it simply outputs to the specified packet_out.egress_port.

```C++
            standard_metadata.egress_spec = hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
```
This is rewritten as follows.
```C++
            if (hdr.packet_out.mcast_grp == 0) { // packet out to specified port
                standard_metadata.egress_spec = hdr.packet_out.egress_port;
            } else { // broadcast to all port, or flood except specified port
                standard_metadata.mcast_grp = hdr.packet_out.mcast_grp; // set multicast flag
                meta.ingress_port = hdr.packet_out.egress_port; // store exception port
            }
```

For this purpose, user metadata is prepared as follows.

```C
struct metadata {
    bit<9> ingress_port;
    bit<7> _pad;
}
```

It is summarized as follows:

- If the Packet-Out does not specify a Multicast Group (0),
  - Output destination is packet_out.egress_port
- If a Multicast Group is specified,
  -  Specify that as the multicast output destination,
  - Set Ingress_port to the port written in packet_out.egress_port
  - The information of packet_out.egress_port is recorded in meta.ingress_port which is user metadata (this is the port number to which the output will be dropped)

In particular, the last step is important and somewhat tricky. (I'm sorry. I wanted to save the field. Read the next section if you want to see how it works.)

As a result, the packets are replicated to all ports by Replication Enigne, and egress processing is performed for each.

#### Egress processing on the switch side

The egress process is easy. If the output destination is the excluded port set above, simply drop it without outputting. Others are output as is.

```C
        if(meta.ingress_port == standard_metadata.egress_port) {
            mark_to_drop(standard_metadata);
        }
```



## Phew...

In this tutorial, we tried to work with the controller via Packet-In / Out. Of course you do not get the performance of the switch in such a way. In the next tutorial, you add flow entries that correspond properly to the host and creates a switch that allows packet exchange without the controller.



### Appendix: To verify the operation of the Packet-Out process

As mentioned above, setting the Multicast Group and egress_port for this switch's Packet-Out processing is somewhat tricky.

- To output to port 3
  - Set hdr.packet_out.egress_port to 3
  - Set hdr.packet_out.mcast_grp to 0 (initial value is 0)
- To output to a port other than port 3 (as Flooding), do as follows
  - Set hdr.packet_out.egress_port to 3
  - Set hdr.packet_out.mcast_grp to 1

It may be easier to understand if you actually check the behavior. The method is shown below.

#### Unicast specified to be output to port 3

I created a Stream Message Request in packetout3.txt to output only to port 3. It can be sent to the switch using the Request() function as follows:

```bash
P4Runtime sh >>> Request("/tmp/packetout3.txt")
packet {
  payload: "\377\377\377\377\377\377\377\377\377\377\377\377\000\0001234567890123456789012345678901234567890123456789012345678901234567890123456789"
  metadata {
    metadata_id: 1    <<<<< egress_port
    value: "\000\003"
  }
  metadata {
    metadata_id: 3    <<<<< mcast_id
    value: "\000\000"
  }
}
```

If you monitor each port of Mininet, you will see that packets are detected only on port 3 (s1-eth3).

#### Multicast specification to output to all ports except port 3

I created a Stream Message Request in packetout3else.txt to output to all ports except port 3. You can send it to the switch using the Request() function:

```bash
P4Runtime sh >>> Request("/tmp/packetout3else.txt")                                                                                            
packet {
  payload: "\377\377\377\377\377\377\377\377\377\377\377\377\000\0001234567890123456789012345678901234567890123456789012345678901234567890123456789"
  metadata {
    metadata_id: 1    <<<<< egress_port
    value: "\000\003"
  }
  metadata {
    metadata_id: 3    <<<<< mcast_id
    value: "\000\001"
  }
}
```

If you monitor each port of Mininet, you will see that packets are detected on ports other than port 3 (s1-eth3).

#### 

## Next Step

#### Tutorial 4: [NanoSwitch04](t4_nanosw04.md)

