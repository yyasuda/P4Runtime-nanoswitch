## Cheat Sheet for those who want to skip the tutorial

Here is a document for anyone who wants to skip the entire Tutorial process and just try nanosw06 straight forward.

### Step by Step

#### Launch Mininet 

Create a situation where three hosts, h1, h2, and h3, are connected to one switch.

```bash
$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

#### Build P4Runtime Shell dev version

We will use a [p4runtime shell](https://github.com/p4lang/p4runtime-shell) Docker Image built with Dockerfile.dev.

```bash
$ git clone https://github.com/p4lang/p4runtime-shell.git
Cloning into 'p4runtime-shell'...
remote: Enumerating objects: 50, done.
(snip...)
Resolving deltas: 100% (101/101), done.
$ cd p4runtime-shell/
$ docker build -t myproj/p4rt-sh-dev -f Dockerfile.dev .
Sending build context to Docker daemon  372.2kB
Step 1/7 : FROM p4lang/p4runtime-sh:latest
(snip...)
Successfully built 5ddb6ed47ba8
Successfully tagged myproj/p4rt-sh-dev:latest
$ docker images
REPOSITORY            TAG                 IMAGE ID            CREATED             SIZE
myproj/p4rt-sh-dev    latest              5ddb6ed47ba8        23 seconds ago      285MB
```

After building, copy the nanosw06 directory tree somewhere, then start p4runtime shell with it like this.

```bash
$ docker run -it -v /tmp/P4runtime-nanoswitch/nanosw06/:/tmp/ myproj/p4rt-sh-dev /bin/bash
root@9f0bcd94e736:/p4runtime-sh# source $VENV/bin/activate
(venv) root@9f0bcd94e736:/p4runtime-sh# cd /tmp
(venv) root@9f0bcd94e736:/tmp# ls
context.py  double_send.py  nanosw05.json  nanosw05.p4  nanosw05.p4i  p4info.txt  shell.py
(venv) root@9f0bcd94e736:/tmp# cp context.py shell.py /p4runtime-sh/p4runtime_sh/
(venv) root@9f0bcd94e736:/tmp# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XXX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw05.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>> PacketIn()

```

After PacketIn(), you will see a number of packets destined for 33:33:00:00:00:02, even though you haven't sent any packets, but ignore them.

#### Mininet operation

If you send a ping request, you can see that the ping response is returned correctly.

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.98 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 8.986/8.986/8.986/0.000 ms
mininet>
```

#### P4 RuntimeShell messages

At this time, you can confirm that Packet-In processing is being performed on the controller side.

```bash
P4Runtime sh >>> PacketIn()

........
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<< Packet In of ARP Request
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:03 - port(3)
.
======
packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2  <<<< Packet In of ARP Response
## INSERT ## dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=1
## INSERT ## dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=2
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:03 - port(3)
.....
......  
```

#### Mininet operation

If you send the ping request again, you can see that the ping response is returned correctly. At this time, there is no packet-in message on the P4Runtime Shell side. This means that the packet was wrapped around the switch without going through the controller. Not only that, the response time is about 10 times faster (ARP processing overhead is no longer required too).

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.877 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.877/0.877/0.877/0.000 ms
mininet>
```

#### Check the flow entries on the P4Runtime Shell

You can check the flow entries registered in l2_match_table with PrintTable().

```bash
......^C  <<<< Interrupted by Control-C
Nothing (returned None)

P4Runtime sh >>> PrintTable()                                                                                         
MyIngress.l2_match_table
  dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 action=MyIngress.flooding
  dst=00:00:00:00:00:01 src=00:00:00:00:00:02 action=MyIngress.forward ( 1 )
  dst=00:00:00:00:00:02 src=00:00:00:00:00:01 action=MyIngress.forward ( 2 )

P4Runtime sh >>>
```

If you want to continue sending and receiving packets, execute the PacketIn () function again.





