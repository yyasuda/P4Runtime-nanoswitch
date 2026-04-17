## Cheat Sheet for those who want to skip the Tutorial

This document is provided for those who want to skip all Tutorial steps and simply try nanosw06.

### Step by Step

#### Starting the Mininet environment

Create a setup where three hosts, h1, h2, and h3, are connected to a single switch.

```bash
$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

### Connecting P4Runtime Shell and Mininet

For experiments in this tutorial, use the [p4runtime shell](https://github.com/p4lang/p4runtime-shell) Docker Image. Copy the nanosw06 directory, etc. to your local environment, then start it as follows and run the controller program.

```bash
$ mkdir /tmp/P4runtime-nanoswitch
$ cp -rp nanosw0* /tmp/P4runtime-nanoswitch
$ ls /tmp/P4runtime-nanoswitch
nanosw01	nanosw02	nanosw03	nanosw04	nanosw05	nanosw06
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw01/p4info.txt,/tmp/nanosw01/nanosw01.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> import sys

P4Runtime sh >>> sys.path.append "/tmp/nanosw06"

P4Runtime sh >>> import tutorial

P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```

#### Operations on the Mininet side

In this state, if you send a ping request from Mininet, you can confirm that a correct ping response is returned.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.98 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 8.986/8.986/8.986/0.000 ms
mininet>
```

#### P4 RuntimeShell screen

At this point, you can confirm that Packet-In processing is being performed on the controller side.

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action
send 
...(snip)

packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2
send 
...(snip)
```

#### Operations on the Mininet side

If you send a ping request again, you can confirm that a correct ping response is returned. At this time, no Packet-In message appears on the P4Runtime Shell side, indicating that the packet is forwarded within the switch without passing through the controller. In addition, (together with the fact that ARP processing is no longer required) the response time becomes several times faster.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.877 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.877/0.877/0.877/0.000 ms
mininet>
```

#### Checking flow entries on the P4Runtime Shell side

You can check the flow entries registered in l2_match_table using PrintTable().

```bash
^C  <<<< interrupted with Control-C
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\xff\xff\xff\xff\xff\xff" 
  }
...(snip)
P4Runtime sh >>>
```

If you want to continue sending and receiving packets, run the controller program again.
