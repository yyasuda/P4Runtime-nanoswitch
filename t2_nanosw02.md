## Tutorial 2: NanoSwitch02

In the first Tutorial, an "unfruitful" packet was repeated. When you output to each port, it is better to stop processing if you find that it is going to repeat to the same port as the Ingress_port of the original packet.

### Experiment

#### P4Runtime Shell operation

Terminate the execution of the P4Runtime Shell and replace shell.py with the expanded version of it in nanosw02 directory. 
```python
P4Runtime sh >>> exit
(venv) root@f4f19294589c:/tmp/nanosw01# cd ../nanosw02
(venv) root@f4f19294589c:/tmp/nanosw02# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw02.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```

#### Multicast Group setting remains on the switch side (bug?)

You set up a Multicast Group in Tutorial 1. This setting remains on the Mininet switch after exiting the P4Runtime Shell. Therefore, re-running the P4Runtime Shell, you don't need to reconfigure the Multicast Group. But read() function doesn't work properly (me.read() just shows the replica information recorded in variable me, it doesn't get information from the switch), and insert() with the same id again works without error. However, if you ping it, it duplicates the "Twice" all packets. Strange behavior.

I am not sure that if this Mininet switch behavior is correct as a P4Runtime or simply it is a bug. For now, after restarting the P4Runtime Shell, here's how to delete the Multicast Group id 1 setting left on the switch where the Multicast Group should have been registered before.

```bash
P4Runtime sh >>> MulticastGroupEntry(1).insert()  <<<< first, nsert one

P4Runtime sh >>> MulticastGroupEntry(1).delete()  <<<< next delete will always effective
```

#### Mininet operation

If you send a ping request again here, you can confirm that the ping reply is returned as before.
```bash
mininet> h1 ping -c 1 h2       <<<<<< ping one time from h1 to h2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.51 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.511/1.511/1.511/0.000 ms
mininet> 

```

The monitoring results of each port are shown below. You can see that this also suppresses unnecessary packet repeating.

#####  h1 (s1-eth1)

```bash
12:06:26.632423 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 108, seq 1, length 64
12:06:26.633851 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 108, seq 1, length 64
```

##### h2 (s1-eth2)

```bash
12:06:26.633151 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 108, seq 1, length 64
12:06:26.633184 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 108, seq 1, length 64
```

##### h3 (s1-eth3)

```bash
12:06:26.633334 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 108, seq 1, length 64
12:06:26.633996 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 108, seq 1, length 64
```

The following sections describe the behavior of the packet in this experiment.

### The behavior of the packet

See the Egress process in nanosw02.p4. This is the only difference from nanosw01.p4. In nanosw01.p4, the egress process was empty. Just ```apply {} ``` was there.

In other words, as a result of setting as multicast in Ingress processing, each packet for which the output for each duplicated port is set is applied to Egress processing. At this time, if the output destination (standard_metadata.egress_port) is the same as the input port (standard_metadata.ingress_port), the packet is specified to be dropped by mark_to_drop().

```C++
control MyEgress(inout headers hdr, inout metadata meta,
                inout standard_metadata_t standard_metadata)
{
    apply {
        // to prevent to reflect packet the same port of original ingress, just drop it
        if(standard_metadata.egress_port == standard_metadata.ingress_port) {
            mark_to_drop(standard_metadata);
        }
    }
}

```

By this operation, unnecessary packet repeating was eliminated, and correct "Flooding" can be performed.



## Next Step

#### Tutorial 3: [NanoSwitch03](t3_nanosw03.md)

