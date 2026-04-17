## Tutorial 2: NanoSwitch02

最初の Tutorial では「無駄な」パケットのリピートが発生していました。ここでは各ポートへの出力の際に、それが元のパケットの Ingress_port と同じポートへのリピートになると判明したら処理を行わないようにします。

### 実験

#### P4Runtime Shell 側操作

一旦 P4Runtime Shell の実行を終わり、スイッチプログラムを nanosw02 に切り替えて再実行してください。
```bash
P4Runtime sh >>> exit
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw02/p4info.txt,/tmp/nanosw02/nanosw02.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```

#### スイッチ側に Multicast Group の設定が残る（バグ？）

Tutorial 1 で Multicast Group を設定しました。この設定は P4Runtime Shell を終了したあとも Mininet のスイッチに残っています。そのため、P4Runtime Shlell を再実行しても、Multicast Group の設定をもう一度行う必要はありません。しかし実際には read() は機能しませんし、再度同じ id で insert() してもエラーにはなりません。そのくせ、ping を飛ばすと「二度」パケットを複製します。

この Mininet のスイッチ側の挙動が P4Runtime として正しいのか、あるいはバグなのか私には分かりません。とりあえず P4Runtime Shell を再起動して、以前に Multicast Group を登録したはずのスイッチに残されている Multicast Group id 1 の設定を消去する方法だけ以下に示しておきます。

```bash
P4Runtime sh >>> MulticastGroupEntry(1).insert()  <<<< まず一度（意味なく）insert しておく

P4Runtime sh >>> MulticastGroupEntry(1).delete()  <<<< 次に delete すると必ず消える
```

このチュートリアルではこのバグのような動作を利用して、P4Runtime Shell を再起動しても Multicast 設定が残っているものとして進めます。もし Mininet 側が修正されてこの「設定が残る」ような振る舞いがなくなった場合は、毎回 Multicast Group の設定処理をする必要があります。

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

つまり nanosw01 と nanosw02 の P4 プログラムの違いによって挙動が変わったのです。この実験でのパケットの動きについて説明します。

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

