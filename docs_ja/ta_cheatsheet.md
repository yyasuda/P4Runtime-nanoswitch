## Tutorial をスキップしたい人のための Cheat Sheet

すべての Tutorial 過程をスキップして、とにかく nanosw06 を簡単に試したい、という人のためのドキュメントをつけておきます。

### 手順

#### Mininet 環境の立ち上げ

一つのスイッチに h1, h2, h3 の三つのホストが接続された状況を作ります。

```bash
$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

### P4Runtime Shell と Mininet の接続

このチュートリアルでの実験には、[p4runtime shell](https://github.com/p4lang/p4runtime-shell) Docker Image を使います。nanosw06 ディレクトリなどを手元にコピーしてから、このようにして起動し、コントローラ・プログラムを実行してください。

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


#### Mininet 側操作

この状態で Mininet 側で ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.98 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 8.986/8.986/8.986/0.000 ms
mininet>
```

#### P4 RuntimeShell 側画面

このとき、コントローラ側で Packet-In 処理が行われていることが確認できます。

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

#### Mininet 側操作

もう一度 ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。このとき、P4Runtime Shell 側には Packet-In によるメッセージが出ず、パケットがコントローラを介さず、スイッチで折り返されたことが分かります。それだけでなく（ARP処理が不要なことと合わせて）応答時間が数倍ほど早くなっています。

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.877 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.877/0.877/0.877/0.000 ms
mininet>
```

#### P4Runtime Shell 側でフロー・エントリ内容を確認する

PrintTable() で l2_match_table に登録されたフロー・エントリを確認できます。

```bash
^C  <<<< Control-C で中断
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\xff\\xff\\xff\\xff\\xff\\xff" 
  }
...(snip)
P4Runtime sh >>>
```

さらにパケットの送受信を続けたい場合はコントローラ・プログラムを再び実行してください。



