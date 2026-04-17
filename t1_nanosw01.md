## Tutorial 1: NanoSwitch01

First, as the simplest switch, we will create one that repeats all received packets to all ports. In P4, the Multicast Group function is provided for such purposes.

### Experiment

#### Operations on the P4Runtime Shell side

Here we configure a Multicast Group. By using P4Runtime's MulticastGroupEntry, a single packet can be replicated and output to multiple ports. Note that the following operations assume that you have already connected to Mininet using the nanosw01 program in [Tutorial 0:](t0_nanosw00.md).

For example, switch s1 has three ports: port 1, 2, and 3. By registering all of these into a single Multicast Group and setting the packet output destination to this Multicast Group, so-called flooding is performed.

The following operation creates a request that associates port 1, 2, and 3 with Multicast Group id 1. When the created request is sent to the switch using the insert() operation, the Multicast Group is configured in the switch.

```python
P4Runtime sh >>> me = MulticastGroupEntry(1)

P4Runtime sh >>> me.add(1).add(2).add(3)
Out[3]: 
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

The first two lines of the above operation can also be written in a single line as follows. (Originally, it should be possible to confirm the registered content with ```me.read()```, but this operation results in an error.)

```bash
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>> me.read()
Out[6]: <p4runtime_sh.shell._EntityBase.read.<locals>._EntryIterator at 0x7fffd86bb0a0>

P4Runtime sh >>> 
```

#### Operations on the Mininet side

With this Multicast Group configured, if you send a ping request, you can confirm that a ping reply is returned.

```bash
mininet> h1 ping -c 1 h2       <<<<<< send a single ping from h1 to h2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.12 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.125/1.125/1.125/0.000 ms
mininet> 
```

However, at this time, if you monitor the switch ports with tcpdump, you will observe that packets are excessively reflected. It is easy to start tcpdump as follows.

```bash
$ docker ps | grep p4mn
3d1e484badb8   yutakayasuda/p4mn     "/root/run-p4mn.sh -…"   27 minutes ago   Up 27 minutes   0.0.0.0:50001->50001/tcp, [::]:50001->50001/tcp   kind_gagarin
$ docker exec -it 3d1e484badb8 /bin/bash
root@3d1e484badb8:/tmp# tcpdump -i s1-eth1     <<<< monitor the path between s1 and h1
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on s1-eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
(waiting...)
```

The monitoring results for each port are shown below. Labels are added at the end of each line with #.

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

Next, we explain the packet behavior in this experiment.

### Packet Behavior

Look at the Ingress processing in nanosw01.p4. The default_action is set to flooding. Since the l2_match_table is currently empty, all packets are processed by flooding.

The contents of the flooding() function simply set standard_metadata.mcast_grp to 1. This causes packets to be output to all ports registered in multicast_group_id: 1 configured earlier.

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

This processing results in the following packet exchanges.

- By ping h1 -> h2, the first packet observed on the h1 monitor (labeled #1-1 at the right end of the monitoring results above) is generated
- This packet is replicated to all ports and observed on all interfaces. That is, packets #1-1, #2-1, #3-1 correspond to this
- h2 returns a reply to the received ICMP Echo Request. This is #2-3
- This packet is replicated to all ports. These are #1-3, #2-3, #3-2

Note that multicast group id does not have to be 1; other numbers can be used. However, 0 cannot be used. If 0 is set, it means that the packet output is not multicast.



## Next Step

#### Tutorial 2: [NanoSwitch02](t2_nanosw02.md)