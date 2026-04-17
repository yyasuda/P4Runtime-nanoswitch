## Tutorial 3: NanoSwitch03

今回試すスイッチは、スイッチ側にフロー・テーブルを作って未知のホストに対応します。フロー・テーブルにエントリを登録する処理のために、コントローラ（P4Runtime Shell）に少し機能を追加します。

### 実験

#### P4Runtime Shell 側操作

一旦 P4Runtime Shell の実行を終わり、今度は nanosw03 スイッチプログラムを使って P4Runtime Shell を再起動してください。

```python
P4Runtime sh >>> exit
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw03/p4info.txt,/tmp/nanosw03/nanosw03.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> 
```

その後、以下のようにして /tmp/nanosw03 以下にある tutorial.py にあるコントローラプログラムを起動します。
```python
P4Runtime sh >>> import sys

P4Runtime sh >>> sys.path.append "/tmp/nanosw03"

P4Runtime sh >>> import tutorial

P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```
#### Mininet 側操作

ここで再び ping 要求を送ると、先ほど同様に ping 応答が帰ってくることが確認できます。
```bash
mininet> h1 ping -c 1 h2       <<<<<< h1 から h2 への ping を一回だけ送る
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=6.23 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 6.233/6.233/6.233/0.000 ms
mininet> 
```

以下に各ポートのモニタリング結果を示します。これもまた無駄なパケットの折り返しが抑制されていることが分かります。

#####  h1 (s1-eth1)

```bash
12:30:55.734450 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.740638 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

##### h2 (s1-eth2)

```bash
12:30:55.738186 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.738210 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

##### h3 (s1-eth3)

```bash
12:30:55.738150 IP 10.0.0.1 > 10.0.0.2: ICMP echo request, id 129, seq 1, length 64
12:30:55.740679 IP 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 129, seq 1, length 64
```

#### P4 RuntimeShell 側画面

このとき、以下のような表示が出ていることが確認できます。往復した二つのパケットがどちらも Packet-In 処理されていることが分かります。

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=1    <<<< 一つ目のパケットの処理
send 
 payload: "\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x00\\x00\\x01\\x08\\x00\\x45\\x00\\x00\\x54\\x99\\xea\\x40\\x00\\x40\\x01\\x8c\\xbc\\x0a\\x00\\x00\\x01\\x0a\\x00\\x00\\x02\\x08\\x00\\x74\\x49\\x00\\xa1\\x00\\x01\\x70\\xcc\\xe0\\x69\\x00\\x00\\x00\\x00\\x64\\x0b\\x0f\\x00\\x00\\x00\\x00\\x00\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f\\x20\\x21\\x22\\x23\\x24\\x25\\x26\\x27\\x28\\x29\\x2a\\x2b\\x2c\\x2d\\x2e\\x2f\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37"
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


packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2    <<<< 二つ目のパケットの処理
send 
 payload: "\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x02\\x08\\x00\\x45\\x00\\x00\\x54\\xfc\\xbf\\x00\\x00\\x40\\x01\\x69\\xe7\\x0a\\x00\\x00\\x02\\x0a\\x00\\x00\\x01\\x00\\x00\\x7c\\x49\\x00\\xa1\\x00\\x01\\x70\\xcc\\xe0\\x69\\x00\\x00\\x00\\x00\\x64\\x0b\\x0f\\x00\\x00\\x00\\x00\\x00\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f\\x20\\x21\\x22\\x23\\x24\\x25\\x26\\x27\\x28\\x29\\x2a\\x2b\\x2c\\x2d\\x2e\\x2f\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37"
metadata {
  metadata_id: 1 ("egress_port")
  value: "\\x00\\x02"
}
metadata {
  metadata_id: 2 ("_pad")
  value: "\\x00"
}
metadata {
  metadata_id: 3 ("mcast_grp")
  value: "\\x00\\x01"
}

^C                <<<< Control-C で中断
P4Runtime sh >>>
```

次にこの実験でのパケットの動きについて説明します。

### パケットの動き

#### 概略

このスイッチは受け取ったパケットをすべてコントローラ経由で他のポートにフラッディングします。下の図は host 1 が出したパケットが、コントローラ経由で host 2, host 3 に送られるようすを示したものです。

<img src="../packet_path.png" alt="attach:(packet path)" title="Packet Path" width="300">

少し詳しく説明します。

1. host 1 が出したパケットはコントローラに向けた Packet-In として出力する
2. コントローラはこれにMulticastGroup id 1 を設定して、Packet-Out する
3. スイッチはCPU_PORTからこれを受け取り、Multicastとして複製し、出力する
4. ただし元々の入力ポート（port 1）と同じポートに出力することになったパケットはドロップする

この動きを実現するために、nanosw03.p4 に幾つかの修正を加えました。パケットの流れに沿って説明します。

#### Processing performed to Packet-In

l2_match_table テーブルの default_action は to_controller であり、現在のところフローテーブルは空なので、すべてのパケットが Controller に Packet-In されることになります。flooding action は使用しません。

```C++
    action to_controller() {
        standard_metadata.egress_spec = CPU_PORT;
        hdr.packet_in.setValid();
        hdr.packet_in.ingress_port = standard_metadata.ingress_port;
    }
    table l2_match_table {
        key = {
            hdr.ethernet.dstAddr: exact;
            hdr.ethernet.srcAddr: exact;
        }
        actions = {
            forward;
            to_controller;
            // flooding;
        }
        size = 1024;
        default_action = to_controller;
    }
```
この Packet-In 処理は先ほど置き換えた shell.py の中に実装されています。以下に主要な部分だけ抜粋して示します。
```Python
def my_packetin(pin):
    global macTable
    payload = pin.packet.payload #パケットのボディ
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = pin.packet.metadata[0].value
    print("\npacket-in: dst={0} src={1} port={2}"
          .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port,'big')))
    mcast_grp = '0x0001'
    out_port = str(int.from_bytes(port,'big'))
    my_packetout(out_port, mcast_grp, payload)
    
def controller_daemon(packet_in, my_packetin=None, args=None):
    if my_packetin is None:
        while True:
            try:
                print(packet_in.packet_in_queue.get(block=True))
            except KeyboardInterrupt:
                break
    else:
        while True:
            try:
                pin = packet_in.packet_in_queue.get(block=True)
                my_packetin(pin)
            except KeyboardInterrupt:
                break
```

つまりpacket_in.packet_in_queue.get() 関数が StreamMessage Response を待ち受け、受信すると受け取った Packet-In パケットを引数に与えて、my_packetin() 関数を呼び出します。

my_packetin() 関数は無条件に受け取ったパケットに、Multicast Group の情報(1) と、元の Ingress_port の情報をつけてmy_packetout() 関数に渡します。

#### Packet-Out に関連する動き

以下に packet_out ヘッダと my_packetout() 関数の実装を示します。packet_out ヘッダにはMulticast Groupの情報が追加されています。

```C++
@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port;
    bit<7> _pad;
    bit<16> mcast_grp; 
}
```

```python
def my_packetout(port, mcast_grp, payload):
    packet = PacketOut(payload)
    packet.metadata['egress_port'] = port
    packet.metadata['mcast_grp'] = mcast_grp
    packet.send()
    print('send \n', packet)
```

この my_packetout() 関数は、とても単純に packet_out ヘッダをセットしてスイッチに送り出すだけのものです。

#### 受信したスイッチ側でのIngress処理

スイッチ側はこの追加された packet_out ヘッダ、つまり mcat_grp に反応するために、nanosw03.p4 側の Packet-Out 処理を修正しています。
元は以下のような記述でした。つまり Packet-Out （CPU_PORT から来たパケット）だったら、そこに指定された packet_out.egress_port に出力するだけのものです。

```C++
            standard_metadata.egress_spec = hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
```
ここを以下のように書き換えています。
```C++
            if (hdr.packet_out.mcast_grp == 0) { // packet out to specified port
                standard_metadata.egress_spec = hdr.packet_out.egress_port;
            } else { // broadcast to all port, or flood except specified port
                standard_metadata.mcast_grp = hdr.packet_out.mcast_grp; // set multicast flag
                meta.ingress_port = hdr.packet_out.egress_port; // store exception port
            }
            hdr.packet_out.setInvalid();
```

このために以下のようにユーザメタデータを用意しています。

```C
struct metadata {
    bit<9> ingress_port;
    bit<7> _pad;
}
```

つまり、

- もし Packet-Out にMulticast Groupの指定がない (0) なら、
  - 出力先は packet_out.egress_port となる
- もしMulticast Groupの指定があれば、
  -  マルチキャストの出力先としてそこを指定し、
  - ユーザメタデータである meta.ingress_port に、出力をドロップする対象となるポートの情報（packet_out.egress_port）を記録する

特に最後の処理は重要かつ、いくらかトリッキーなものになっています。（ごめんなさい。フィールドを節約したかったんです。動作を確認したい人は下の補足を読んで下さい。）

この結果、パケットは Replication Enigne によってすべてのポートに複製され、それぞれに対してEgress処理が行われます。

#### スイッチ側でのEgress処理

Egress 処理は簡単です。出力先が上で設定した除外ポートであれば、単に出力せずドロップします。それ以外のものはそのまま出力されます。

```C
        if(meta.ingress_port == standard_metadata.egress_port) {
            mark_to_drop(standard_metadata);
        }
```



## ふぅ。

この Tutorial では、Packet-In/Out を介したコントローラとの協調作業を試しました。もちろんこんなことをしていてはスイッチとしてまったく性能が出ません。次の Tutorial では、ちゃんとホストに対応するフロー・エントリを追加し、コントローラを介さないパケットの交換を実現するスイッチを作ります。



### 補足：Packet-Out処理の実験

上に書いたように、このスイッチのPacket-Out 処理に対するMulticast Group と egress_port の設定はいくらかトリッキーです。

- port 3 に出力するためには、以下のようにする
  - hdr.packet_out.egress_port を 3 にする
  - hdr.packet_out.mcast_grp を 0 にする（初期値が 0 ）
- port 3 以外に出力する（Floodingする）ためには、以下のようにする
  - hdr.packet_out.egress_port を 3 にする
  - hdr.packet_out.mcast_grp を 1 にする

実際に挙動を確認すると分かりやすいかもしれませんが、そのテストはちょっと簡単ではないのでここには書かないでおきます。

#### 

## Next Step

#### Tutorial 4: [NanoSwitch04](t4_nanosw04.md)

