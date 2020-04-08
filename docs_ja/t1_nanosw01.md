## Tutorial 1: NanoSwitch01

まず最初に、最も簡単なスイッチとして、届いたパケットのすべてを全ポートにリピートするものを作ります。P4 では、そうした用途のために Multicast Group 機能が用意されています。

### 実験

#### P4Runtime Shell 側操作

ここでは Multicast Group の設定を行います。

スイッチ s1 は port 1, 2, 3 の三つのポートを持っています。これらをすべて一つの Multicast Group に登録し、そこにパケットを出力することで、いわゆる Flooding が行われます。

```python
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>> me.read()
Out[5]: 
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

#### Mininet 側操作

この Multicast Group の設定ができた状態で ping 要求を送ると、ともかく ping 応答が帰ってくることが確認できます。
```bash
mininet> h1 ping -c 1 h2       <<<<<< h1 から h2 への ping を一回だけ送る
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.12 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.125/1.125/1.125/0.000 ms
mininet> 
```

但しこのとき、tcpdump などでスイッチのポートを見張っていると、過剰にパケットが跳ね返されていることが確認できるでしょう。tcpdump は以下のようにして起動するのが簡単です。

```bash
$ docker ps | grep p4mn 
d481bf29d905        opennetworking/p4mn   "mn --custom bmv2.py…"   6 minutes ago       Up 6 minutes        0.0.0.0:50001->50001/tcp, 50002-50999/tcp   great_carson
$ docker exec -it d481bf29d905 /bin/bash
root@d481bf29d905:~# tcpdump -i s1-eth1      <<<< s1 と h1 の間の経路をモニタリングする
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on s1-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
(waiting...)
```

以下に各ポートのモニタリング結果を示します。各行の最後に # 付きでラベルを振ってあります。

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

次にこの実験でのパケットの動きについて説明します。

### パケットの動き

nanosw01.p4 の Ingress 処理を見て下さい。default_action が flooding に設定されています。今は l2_match_table は空ですから、すべてのパケットが flooding 処理されます。

flooding() 関数の中身は、standard_metadata.mcast_grp を 1 に設定するだけですが、これで先ほど設定した multicast_group_id: 1 に登録された全ポートにパケットが出力されます。

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

この処理によって以下のようなパケットの往復が発生します。

- ping h1 -> h2 によって、h1 側モニタの一番めのパケット（上のモニタリング結果の右端に ```#1-1``` とラベルされたパケット）が観測されます
- このパケットは全ポートに複製され、それが全てのインタフェイスで観測されます。つまり ```#1-1, #2-1, #3-1``` パケットがそれです。
- h2 は届いた ICMP Echo Request に対して reply を返します。これが ```#2-3``` です。
- このパケットは全ポートに複製されます。```#1-3, #2-3, #3-2``` がそれです。



## Next Step

#### Tutorial 2: [NanoSwitch02](t2_nanosw02.md)