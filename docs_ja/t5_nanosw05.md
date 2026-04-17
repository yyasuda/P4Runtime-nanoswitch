## Tutorial 5: NanoSwitch05

ところでこれまでは ARP パケットの処理をしていませんでした。ブロードキャストを無視していたわけです。ここではブロードキャストが届いたら、それをフロー・エントリに追加して、以後コントローラに来ないようにします。

### 実験

#### Mininet 側操作

Mininetを終了し、--arp オプションを外して再起動します。これでARPを最初に吐いてくれます。

```bash
mininet> exit
*** Stopping 0 controllers
(snip...)
*** Done
completed in 1063.313 seconds
$

$ docker run --privileged --rm -it -p 50001:50001 -e IPV6=false yutakayasuda/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

#### P4Runtime Shell 側操作

まず一旦 P4Runtime Shell の実行を終わり、nanosw05 以下にある nanosw05 スイッチプログラムを使って P4Runtime Shell を再起動してください。

```python
P4Runtime sh >>> exit
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw05/p4info.txt,/tmp/nanosw05/nanosw05.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```

今回は Mininet 側を再起動したので、Multicast Group の再設定をスキップしないように。

```python
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>>
```

その後、以下のようにして /tmp/nanosw05 以下にある tutorial.py にあるコントローラプログラムを起動します。

```python
P4Runtime sh >>> import sys

P4Runtime sh >>> sys.path.append "/tmp/nanosw05"

P4Runtime sh >>> import tutorial

P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```

#### 再び Mininet 側操作

ここで再び ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。

```bash
mininet> h1 ping h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=2.33 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.866 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.919 ms
^C
--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2013ms
rtt min/avg/max/mdev = 0.866/1.372/2.331/0.678 ms
mininet> 
```
このとき Mininet のポートをモニタリングをしていると、ICMPパケットだけではなく ARP パケットが往復していることを確認できるでしょう。

```bash
00:58:51.242280 ARP, Request who-has 10.0.0.1 tell 10.0.0.2, length 28
00:58:51.242330 ARP, Reply 10.0.0.1 is-at 00:00:00:00:00:01 (oui Ethernet), length 28
00:59:57.322896 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 1, length 64
00:59:57.325070 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 1, length 64
00:59:58.325092 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 2, length 64
00:59:58.325904 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 2, length 64
00:59:59.335442 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 106, seq 3, length 64
00:59:59.336214 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 106, seq 3, length 64
```

#### P4 RuntimeShell 側画面

同時に、P4 Runtime Shell 側では以下のような表示が出ていることが確認できます。最初の ARP request パケットは Packet-In でコントローラに戻され、flooding となるよう Multicast 指定して Packet-Out されます。二つ目の ARP response パケットは Packet-In 処理で port 1 への転送となるよう Packet-Out されます。並行してブロードキャストと h1 -> h2、h2 -> h1 向けの三つのフロー・エントリが設定され、これ以降はコントローラに Packet-In されることがなくなっています。
```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action
send 
 payload: "\\xff\\xff\\xff\\xff\\xff\\xff\\x00\\x00\\x00\\x00\\x00\\x01\\x08\\x06\\x00\\x01\\x08\\x00\\x06\\x04\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x01\\x0a\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x0a\\x00\\x00\\x02"
metadata {
  metadata_id: 1 ("egress_port")
  value: "\\x00\\x01"
}
metadata {
  metadata_id: 2 ("_pad")
  value: "\\x00"
}
metadata {
  metadata_id: 3 ("mcast_grp")
  value: "\\x00\\x01"
}


packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2
send 
 payload: "\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x02\\x08\\x06\\x00\\x01\\x08\\x00\\x06\\x04\\x00\\x02\\x00\\x00\\x00\\x00\\x00\\x02\\x0a\\x00\\x00\\x02\\x00\\x00\\x00\\x00\\x00\\x01\\x0a\\x00\\x00\\x01"
metadata {
  metadata_id: 1 ("egress_port")
  value: "\\x00\\x01"
}
metadata {
  metadata_id: 2 ("_pad")
  value: "\\x00"
}
metadata {
  metadata_id: 3 ("mcast_grp")
  value: "\\x00\\x00"
}

^C  <<<< それ以降の ping のパケットは Packet-In されない（Control-C で中断）
P4Runtime sh >>> 

<<<< 以下のようにして l2_match_table に登録されたフロー・エントリを確認することもできる。
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
...(snip)
```

#### テーブルの中身

以下のようにして l2_match_table に登録されたフロー・エントリを確認することができます。一つめがブロードキャストを flooding するためもので、残りの二つが h1, h2 間のパケット往復について forward するためのエントリーです。

```bash
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< ブロードキャストを flooding するためのエントリ
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\xff\\xff\\xff\\xff\\xff\\xff"  <<<< 宛先が "ff:ff:ff:ff:ff:ff" かつ、
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x01"        <<<< 送り元が "00:00:00:00:00:01" の場合は、
  }
}
action {
  action {
    action_id: 16837454 ("MyIngress.flooding")  <<<< flooding 関数を呼び出す
  }
}

table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< h2 -> h1 向けのエントリ
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x01"
  }
}
...(snip)

table_id: 33609159 ("MyIngress.l2_match_table")
match {                                 <<<< h1 -> h2 向けのエントリ
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x02"
  }
}
...(snip)

<<<< 以下のようにテーブルの中身を削除してから、もう一度挙動を見ると良い。
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: a.delete())

```


### パケットの往復とフロー・テーブルの操作

以下、h1 から h2 に対して ping したときに生じるパケットの往復と、内部の処理について説明します。

1. h1から ARP request が出る
2. スイッチはこれをコントローラに packet in する
3. コントローラは宛先をブロードキャスト、送信元が h1 のマッチパターンと、action flodding をフロー・エントリに登録する
4. コントローラは受け取ったパケットを flooding （受け取ったポート以外に向けて packet out）する
5. この 4. によって転送された ARP パケットを h2 が受け取り、これに reply を出す
6. やはりこのパターンはフロー・エントリにないので、コントローラに packet-in する
7. コントローラは宛先 h1、送信元 h2 のパターンを action forward として登録する
8. コントローラは受け取ったパケットを flooding （受け取ったポート以外に向けて packet out）する

これ以降に送られる h1 - h2 間の通信は、すべてコントローラを介さず、スイッチだけで転送されます。Packet-In や Flooding は一切生じません。

### 関係するコード

この動きを実現するために、幾つかの修正を加えました。パケットの流れに沿って説明します。

#### nanosw05.p4

l2_match_table テーブルの action として、しばらく使われていなかった flooding を再び有効にします。ただし、action flooding() の中で、multicast group に 1 をセットし、meta.ingress_port に入力ポート番号を記録してあることを意識してください。

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

#### tutorial.py

この、action flooding をセットする処理は先ほど置き換えた shell.py の中の幾つかの関数に実装されています。以下に主要な部分だけ抜粋して示します。まず PacketIn() 関数関連。

```Python
FLOOD_GRP = '0x0001'
FLOOD_PORT = b'\xff\xff'
def my_packetin(pin):
    global macTable
    payload = pin.packet.payload
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = pin.packet.metadata[0].value

    print("\npacket-in: dst={0} src={1} port={2}"
          .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port,'big')))

    if dstMac == b'\xff\xff\xff\xff\xff\xff':  # broadcast
        if srcMac not in macTable:
            macTable[srcMac] = port
        insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
        my_packetout(str(int.from_bytes(port,'big')), FLOOD_GRP, payload)
    else:  # unicast
        if srcMac not in macTable:
            macTable[srcMac] = port
        if dstMac in macTable:
            insertFlowEntry(dstMac, srcMac, macTable[dstMac])
            insertFlowEntry(srcMac, dstMac, macTable[srcMac])
            out_port = str(int.from_bytes(macTable[dstMac],'big'))
            mcast_grp = '0x0000'
        else:
            out_port = str(int.from_bytes(port,'big'))
            mcast_grp = FLOOD_GRP
        my_packetout(out_port, mcast_grp, payload)

def insertFlowEntry(dstMac, srcMac, port):
    (...snip...)
    if port == FLOOD_PORT: # set action to flooding 
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

つまりmy_packetin() 関数が、受け取ったパケットがブロードキャストであれば、ポート番号を（Floodingすべき処理の目印である）FLOOD_PORT として insertFlowEntry() を呼び出します。そこではポート番号がFLOOD_PORTであれば、action として flooding をつけてフロー・エントリをセットします。もしブロードキャストででなければポート番号は入力ポートとなり、insertFlowEntry() 内では、action として forward をつけてフロー・エントリをセットします。

宛先ホストが存在するポートが判明していた場合は Unicast の指定と、当該ポートの情報をつけて PacketOut() 関数を呼び出します。そうで無い、つまりブロードキャストあるいは宛先ホストのポートが不明の場合は Multicast Group の情報(1) と、元の Ingress_port の情報をつけて PacketOut() 関数を呼び出します。

#### エントリ設定前後での ping 処理時間

ここで再び ping 要求を送ると、先ほど同様に ping 応答が帰ってくることが確認できます。ただ、今度はパケットはスイッチに設定されたフロー・エントリに従って折り返され、コントローラに送られてくることはありません。

その応答時間に注目してください。つまり今回はMininet上のホストは ARP パケットを出しません。コントローラ側でのフロー・エントリの設定や Packet Out による転送処理も無し。スイッチだけで高速に処理が完了していることを確認できるでしょう。私の手元の環境では初回が 3-5ms 程度掛かるのに対して、それ以降は 1ms 以下で完了します。

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.783 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.783/0.783/0.783/0.000 ms
mininet> 
```



## Next Step

#### Tutorial 5: [NanoSwitch06](t6_nanosw06.md)

