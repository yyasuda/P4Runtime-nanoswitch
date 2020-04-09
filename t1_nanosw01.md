## Tutorial 1: NanoSwitch01

First, create the simplest switch that repeats all incoming packets to all ports. P4 provides the Multicast Group function for such purposes.

### Experiment

#### P4Runtime Shell operation

Here you can configure the Multicast Group. By using MulticastGroupEntry of P4Runtime, one packet can be duplicated and output to multiple ports.

For example, switch s1 has three ports, port 1, 2, and 3. By registering them all in one Multicast Group and setting the packet output destination to this Multicast Group. It's the so-called Flooding.

The following operation creates a request to bind ports 1, 2, and 3 to id 1 of the Multicast Group. When the created request is sent to the switch by insert() operation, a Multicast Group is set in the switch.

```python
P4Runtime sh >>> me = MulticastGroupEntry(1)

P4Runtime sh >>> me.add(1).add(2).add(3)
Out[6]: 
multicast_group_entry {
  multicast_group_id: 1
  replicas {
    egress_port: 1
  }
  replicas {
    egress_port: 2
  }
  replicas {
    egress_port: 3
  }
}

P4Runtime sh >>> me.insert()

P4Runtime sh >>> 
```

Note that the first two lines of the above operation can be written together on one line as follows. Also, you can confirm the registered contents by ```me.read ()```.

```bash
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()                                                                                                                   

P4Runtime sh >>> me.read()                                                                                                                     
Out[4]: 
multicast_group_entry {
  multicast_group_id: 1
  replicas {
    egress_port: 1
  }
  replicas {
    egress_port: 2
  }
  replicas {
    egress_port: 3
  }
}

P4Runtime sh >>> 
```

#### Mininet operation

If you send a ping request with this Multicast Group setting, you can confirm that the ping response is returned anyway.
```bash
mininet> h1 ping -c 1 h2       <<<<<< ping from h1 to h2 once
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.12 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.125/1.125/1.125/0.000 ms
mininet> 
```

However, if you watch the switch port with tcpdump or something, you will see that there are too many packets bouncing back. It is easy to start tcpdump as follows:

```bash
$ docker ps | grep p4mn 
d481bf29d905        opennetworking/p4mn   "mn --custom bmv2.py…"   6 minutes ago       Up 6 minutes        0.0.0.0:50001->50001/tcp, 50002-50999/tcp   great_carson
$ docker exec -it d481bf29d905 /bin/bash
root@d481bf29d905:~# tcpdump -i s1-eth1      <<<< monitor the path between s1 and h1
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on s1-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
(waiting...)
```

The monitoring results of each port are shown below. Labels are marked with # at the end of each line.

#####  h1 (s1-eth1)

```bash
11:25:15.981884 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 97, seq 1, length 64 #1-1
11:25:15.982270 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 97, seq 1, length 64 #1-2
11:25:15.982985 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 97, seq 1, length 64 #1-3
```

##### h2 (s1-eth2)

```bash
11:25:15.982295 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 97, seq 1, length 64 #2-1
11:25:15.982312 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 97, seq 1, length 64 #2-2
11:25:15.982807 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 97, seq 1, length 64 #2-3
```

##### h3 (s1-eth3)

```bash
11:25:15.982339 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 97, seq 1, length 64 #3-1
11:25:15.982902 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 97, seq 1, length 64 #3-2
```

The following sections describe the behavior of the packet in this experiment.

### The behavior of the packet

Look at the ingress processing in nanosw01.p4. default_action is set to flooding. Therefore, since l2_match_table is now empty, all packets are flooded.

The flooding() function simply sets standard_metadata.mcast_grp to 1. This will output the packet to all ports registered with multicast_group_id: 1 configured earlier.

```C++
    action flooding() {
        // hardcoded, you must configure multicast-group 1 at runtime
        standard_metadata.mcast_grp = 1;
    }
    table l2_match_table {
        key = {
            standard_metadata.ingress_port: exact;
            hdr.ethernet.dstAddr: exact;
        }
        actions = {
            forward;
            to_controller;
            flooding;
        }
        size = 1024;
        default_action = flooding; // all packets go flooding;
    }

```

This process causes the following round trips of packets:

- ping h1 -> h2 causes the first packet (a packet labeled ```#1-1``` to the right of the end of the monitoring result line above) to be observed on the h1-side monitor
-  This packet is replicated to all ports and observed at all interfaces. So, ```#1-1, #2-1, #3-1``` packets are.
- h2 returns a reply to the ICMP Echo Request. This is ```#2-3```.
-  This packet is replicated to all ports. See; ```#1-3, #2-3, #3-2```.

The Multicast Group id can be any number other than 1. However, you cannot use 0. A value of 0 means that the output of the packet is not Multicast.



## Next Step

#### Tutorial 2: [NanoSwitch02](t2_nanosw02.md)