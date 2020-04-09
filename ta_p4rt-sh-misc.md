## Miscellaneous features added to the modified P4 Runtime Shell

This tutorial was arranged by adding features to the P4 Runtime Shell. It includes all the features that I used in this tutorial, as well as some features that I didn't cover here. Hit the link below to read more. I have described here.



### Adding the entry

First, here is the Write() function, which is included in the original P4Runtime Shell. The Write() function sends a WriteRequest message to the switch. As a result, you can see that two entries for the round trip are registered in the table. If you look at the contents of h1_to_h2.txt, you'll see what kind of message is necessary. This will make it easier to understand what the insertFlowEntry() function in shell.py is doing.

```bash
P4Runtime sh >>> Write("/tmp/h1_to_h2.txt")                                                                                                    

P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: print(a))                                                              
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
```



### Packet-Out processing

Invoke the Request() function. Similar to the Write() function, which was introduced above, read the message content from the specified file and feed it to the switch as StreamMessageRequest message of P4Runtime.
No return value or message is returned. The contents of the message to be sent are printed on the screen.

```bash
P4Runtime sh >>> Request("/tmp/packetout.txt")                                                                                             
packet {
  payload: "\377\377\377\377\377\377\377\377\377\377\377\377\000\0001234567890123456789012345678901234567890123456789012345678901234567890123456789"
  metadata {
    metadata_id: 1
    value: "\000\001"
  }
}

P4Runtime sh >>> 
```



### Packet-In monitoring

You can monitor Packet-In (StreamMessageResponse) by Watch() function. For example, when the Watch () function is executed as follows, it will be in the standby state. (Time out in 3 seconds)

```bash
P4Runtime sh >>> res = Watch()
```

In this state, if you send a packet (which derives a Packet-In) from Mininet as ```h1 ping -c 1 h3```, the Watch() function will display the contents of the received message on the screen. And returns it as a return value.

```bash
P4Runtime sh >>> res = Watch()
Response message is:
packet {
  payload: "\000\000\000\000\000\003\000\000\000\000\000\001\010\000E\000\000T\247J@\000@\001\177[\n\000\000\001\n\000\000\003\010\000\306r\000\252\000\001\3366\215^\000\000\000\000\000z\006\000\000\000\000\000\020\021\022\023\024\025\026\027\030\031\032\033\034\035\036\037 !\"#$%&\'()*+,-./01234567"
  metadata {
    metadata_id: 1
    value: "\000\001"
  }
  metadata {
    metadata_id: 2
    value: "\000"
  }
}
```



