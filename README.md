# P4Runtime-NanoSwitch

A Simple L2 lerning switch development tutorial on P4Runtime

[see Japanese version](docs_ja/README.md)

### Introduction

This tutorial builds a simple switch using the Packet-In/Out functionality of P4Runtime. It also prototypes a simple controller based on the P4Runtime Shell and provides an environment that makes it easy for you to continuously extend its functionality.

## This tutorial does…

In this tutorial, you will try the following four things. In the end, a very simple MAC Learning Switch will be completed.

1. Configuration of Multicast Groups and flooding processing using them
2. Requesting processing to the controller using Packet-In
3. Adding entries to the switch table using Packet-Out
4. Adding functionality to the P4Runtime Shell to conduct these experiments

These experiments are performed in the following environment:

- Use P4Runtime Shell as the controller
- Use Mininet with P4Runtime support as the switch
- Use the open-source p4c for P4 compilation

If you want to skip the tutorial, there is a [shortcut](./ta_cheatsheet.md).

## Step by Step

The steps are shown one by one below. It is recommended to try them in order.

### Tutorial 0: [Preparing the Environment](./t0_prepare.md)

Start Mininet and connect the P4Runtime Shell, which acts as a controller, to it.

### Tutorial 1: [NanoSwitch01](./t1_nanosw01.md)

Repeat all received packets to all ports
- Configure a Multicast Group and output to it

### Tutorial 2: [NanoSwitch02](./t2_nanosw02.md)

Prevent the ingress port from being included in the repeat target
- Drop multicast packets if the port number is the same as the ingress port

### Tutorial 3: [NanoSwitch03](./t3_nanosw03.md)

Create a flow table on the switch side to handle unknown hosts
- Unknown packets are sent as Packet-In
- Packets received via Packet-In are sent back as Packet-Out to repeat to all ports

### Tutorial 4: [NanoSwitch04](./t4_nanosw04.md)

Create a host table on the controller side to handle known hosts
- For communication between known host pairs, add entries for both directions to the flow table
- After this, packet forwarding in both directions is handled by the switch alone without involving the controller

### Tutorial 5: [NanoSwitch05](./t5_nanosw05.md)

Add broadcast processing, which was ignored in nanosw04

- When a broadcast occurs, add the corresponding entry to the flow table
- By supporting ARP, it will behave more like a normal switch

### Tutorial 6: [NanoSwitch06](./t6_nanosw06.md)

Handle errors that occur when adding entries to the flow table cannot be completed in time

- If duplicate registration occurs, ignore the error

## Next Step

The switch created here prioritizes making P4Runtime easy to understand and experiment with. Therefore, it is quite incomplete in terms of functionality, and the following issues can be easily identified. Why not try adding these yourself?

- In actual switch operation, it is common to replace host X from port 1 to port 2 on the same switch. However, this switch does not take this into account, and after replacement, packets can no longer be exchanged.

- Since there is a limit to the number of entries that can be registered, flow entries that have not seen traffic for a while should be removed.

- In a typical L2 Learning Switch, it is sufficient to remember only which port the destination host resides on, and there is no need to maintain entries per flow. However, to achieve this in P4, two tables are required: one matching on source MAC and another matching on destination MAC + port. Why not try creating a switch that matches these two tables in sequence?

## Appendix

### Sending RAW packets

Mininet provides tools such as ping, which allow you to easily send packets without generating ARP, etc. However, in experiments using real devices such as a Wedge Switch, you may want to send arbitrary packets from the Wedge itself (OpenNetworkLinux) or from a Windows/Mac connected to a Wedge port. Tools for such cases are provided below.

- [How to Send RAW Packets](ta_rawsend.md)

### CPU port modification

CPU port information is located at the beginning of nanoswXX.p4. Modify the following definition as necessary and recompile.

```C++
#define CPU_PORT 255
```