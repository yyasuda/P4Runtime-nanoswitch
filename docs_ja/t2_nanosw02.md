## Tutorial 2: NanoSwitch02

最初の Tutorial では「無駄な」パケットのリピートが発生していました。ここでは各ポートへの出力の際に、それが元のパケットの Ingress_port と同じポートへのリピートになると判明したら処理を行わないようにします。

### 実験

#### P4Runtime Shell 側操作

一旦 P4Runtime Shell の実行を終わり、スイッチプログラムを nanosw02 に切り替えて再実行してください。
```python
P4Runtime sh >>> exit
(venv) root@f4f19294589c:/tmp/nanosw01# cd ../nanosw02
(venv) root@f4f19294589c:/tmp/nanosw02# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw02.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```

#### Mininet 側操作

ここで再び ping 要求を送ると、先ほど同様に ping 応答が帰ってくることが確認できます。
```bash
mininet> h1 ping -c 1 h2       <<<<<< h1 から h2 への ping を一回だけ送る
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.51 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.511/1.511/1.511/0.000 ms
mininet> 

```

以下に各ポートのモニタリング結果を示します。今度はどのポートにも 2 パケットずつ出力されており、無駄なパケットの折り返しが抑制されていることが分かります。

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

次にこの実験でのパケットの動きについて説明します。

### パケットの動き

nanosw02.p4 の Egress 処理を見て下さい。先ほどの nanosw01.p4 との違いはここだけです。nanosw01.p4 では、Egress 処理は空っぽ、```apply { }``` となっていました。

つまり Ingress 処理でマルチキャストとして設定した結果、複製された各ポート向けの出力を設定されたパケットがそれぞれ Egress 処理に掛かります。このとき、出力先（standard_metadata.egress_port）が入力ポート（standard_metadata.ingress_port）と同じであれば、そのパケットは mark_to_drop() によってドロップ指定しています。

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

この操作によって、無駄なパケットのリピートが無くなり、正しい "Flooding" が行えるようになりました。



## Next Step

#### Tutorial 3: [NanoSwitch03](t3_nanosw03.md)

