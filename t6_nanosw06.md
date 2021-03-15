## Tutorial 6: NanoSwitch06

It takes time for a flow entry to be created in response to a Packet-In sent by a packet destined for a broadcast address or an unknown address. If another packet is sent to the same address before the entry is set, the controller will try to INSERT twice and get an error. A typical case would be two broadcast packets sent in succession from a host. This is a normal situation, such as ARP Requests for two hosts.

There are many possible workarounds, but this section will give you the simplest workaround. In other words, when adding a flow entry, if double registration occurs, the error is ignored.

### Experiment

#### double_send.py

Below is the Python code that sends two broadcast packets in a row. You can also adjust the sleep() time in your code to see how long it takes to complete single flow entry. As you can see from the destination interface and srcMac, this program produces packets equivalent to those sent from the h1 host.

```python
import socket
import time
iface = 'h1-eth0'
dstMac = b'\xff\xff\xff\xff\xff\xff'
srcMac = b'\x00\x00\x00\x00\x00\x01'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
print('send #1 packet.')
s.send(packet)
time.sleep(1)
print('send #2 packet.')
s.send(packet)
print('done.')
s.close()
```

#### Mininet operation

Follow the nanosw05 tutorial to run the Mininet / P4Runtime Shell in the same environment. Then, place the above program under /root in the Mininet environment and execute it as follows.

```bash
mininet> h1 python double_send.py
send #1 packet. <<< 1 second wait time after this display appears
send #2 packet.
done.
mininet> 
```

このパケットがただしく他のホスト、つまり h2, h3 に転送されていることを確認するには、h2 あるいは h3 側でモニタリングする必要があります。（モニタリング操作については [NanoSwitch01](t1_nanosw01.md) を参照してください。）

#### P4 RuntimeShell display

Since there is no change in the switch program this time, nanosw05.p4 is used as it is.

When you execute the double_send.py program as above, you can see the following messages. The arrival of the first packet created a flow entry, with match pattern of broadcast destination and h1 (00: 00: 00: 00: 00: 01) source. The second packet sent 1 sec later is processed according to flow entry, it will not Packet-In. You can see the packets wrapped in the switch by monitoring the h2 and h3 interfaces.

```bash
P4Runtime sh >>> PacketIn()                                                                                                                     
.......
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
......
```

#### Modify double_send.py 

In this state, modify the code of double_send.py so that the second packet is sent without waiting. You can comment out the sleep() line as follows:

```python
print('send #1 packet.')
s.send(packet)
# time.sleep(1)    <<<< commented out
print('send #2 packet.')
s.send(packet)
```

#### Resend by Mininet

Use this to perform the send operation again on Mininet.

```bash
mininet> h1 python double_send.py
send #1 packet. <<< no wait time
send #2 packet.
done.
mininet> 
```

#### P4 RuntimeShell display

This time you will get the following error and the P4Runtime Shell will stop.

```bash
P4Runtime sh >>> PacketIn()

======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<< 1st packet arrived
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action  <<<< set the flow entry 
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
.
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<< 2nd packet arrived
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action  <<<< try to set the flow entry again, get an error as follows;
---------------------------------------------------------------------------
P4RuntimeWriteException                   Traceback (most recent call last)
<ipython-input-1-9a9af7272159> in <module>
----> 1 PacketIn()

/p4runtime-sh/p4runtime_sh/shell.py in PacketIn()
   2427                 # print("\nResponse message is:")
   2428                 # print(rep)
-> 2429                 packetin_process(rep)
   2430                 # return rep # if you want to check the response, just return
   2431     except KeyboardInterrupt:

/p4runtime-sh/p4runtime_sh/shell.py in packetin_process(pin)
   2389         if srcMac not in macTable:
   2390             macTable[ srcMac ] = port
-> 2391         insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
   2392         PacketOut(port, FLOOD_GRP, payload)
   2393     else: # when destination is unicast, do forwarding

/p4runtime-sh/p4runtime_sh/shell.py in insertFlowEntry(dstMac, srcMac, port)
   2351 
   2352     # print(req)
-> 2353     client.write(req)
   2354 
   2355 # macTable = [ mac: port ] - store mac and port of source host

/p4runtime-sh/p4runtime_sh/p4runtime.py in handle(*args, **kwargs)
    122             if e.code() != grpc.StatusCode.UNKNOWN:
    123                 raise e
--> 124             raise P4RuntimeWriteException(e) from None
    125     return handle
    126 

P4RuntimeWriteException: Error(s) during Write:
	* At index 0: ALREADY_EXISTS, 'Match entry exists, use MODIFY if you wish to change action'

```
If you check the flow entry content just to be sure, it has been set to flooding for broadcast packet is registered correctly.

```bash
P4Runtime sh >>> PrintTable("MyIngress.l2_match_table")                                                                                         
MyIngress.l2_match_table
  dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 action=MyIngress.flooding

P4Runtime sh >>>                                                                                                        
```

So this time, the second packet arrives at the switch earlier than the Packet-In processing of the first packet registration. Then, this second packet makes Packet-In again, and the process of registering the exact same flow entry twice is executed. However, the write() process for that failed and caused a P4RuntimeWriteException error.

### Error handling

There are many possible workarounds, but this section will give you the simplest workaround. In other words, when adding a flow entry, if double registration occurs, the error is ignored.

#### shell.py

It is the insertFlowEntry () function in shell.py that raises the error. We want to correct the following parts. Originally it was the following single line.

```python
def insertFlowEntry(dstMac, srcMac, port):
    ...(snip)...
    client.write(req)
```
Add error handling processing here as follows.
```python
    try:
        client.write(req)
    except P4RuntimeWriteException as e:
        if e.errors[0][1].canonical_code == code_pb2.ALREADY_EXISTS:
            print("already exists. ignore this.")
        else:
            print(e)
            raise e
```
In other words, for an error that is simply double-registered, just notice a message and ignore it. Except ALREADY_EXISTS error will directly raise as an error. To add this code, the following two lines are added at the beginning of shell.py.

```python
from p4runtime_sh.p4runtime import P4RuntimeWriteException
from google.rpc import status_pb2, code_pb2 
```

#### Display on the modified P4 Runtime Shell side

Now, use the modified shell.py (under nanosw06 directory) to restart the P4Runtime Shell and run double_send.py again on the Mininet. The following messages will be displayed, and it can be confirmed that the program does not stop even the double registration has occurred.

```bash
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<<< 1st packet arrived
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action <<<< set the flow entry 
macTable (mac - port)
 00:00:00:00:00:01 - port(1)

.
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<<< 2nd packet arrived
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action <<<< set the flow entry again
already exists. ignore this.   <<<<< this time, error occurs but ignored. no stop.
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
.........
```

It's still incomplete as a switch, but I think we've covered what we should do as a P4-based switch with a controller.



You have completed the series of tutorials. Congratulations!

## Next Step

Is [this](README.md#next-step) good for the next?

