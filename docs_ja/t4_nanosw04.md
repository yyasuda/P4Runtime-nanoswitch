## Tutorial 4: NanoSwitch04

コントローラ側にホスト・テーブルを作って既知のホストに対応します。つまり既知のホスト・ペアの通信についてはフローテーブルに往復ぶんのエントリを追加します。それ以降はコントローラを介さず、スイッチだけで往復パケットの転送が行われます。

###  ショートカットしてここから始める人のために

このテストのためには、以下の作業が必要です。

1. P4Runtime Shell の起動と Mininet への接続 - see; Tutorial 0: [実験環境の準備](./t0_prepare.md)
2. Multicast Group の設定 - see; Tutorial 1: [NanoSwitch01](./t1_nanosw01.md)
   それがないとFloodingが行われません。そして（目に見える）エラーも発生しないため、何故動かないのか分からなくなります。

### 実験

#### P4Runtime Shell 側操作

一旦 P4Runtime Shell の実行を終わり、機能追加された shell.py と置き換えます。

```python
P4Runtime sh >>> exit
(venv) root@1923f14d3a08:/tmp/nanosw03# cd ../nanosw04
(venv) root@1923f14d3a08:/tmp/nanosw04# cp shell.py /p4runtime-sh/p4runtime_sh/shell.py 
(venv) root@1923f14d3a08:/tmp/nanosw04# cp context.py /p4runtime-sh/p4runtime_sh/context.py 
(venv) root@1923f14d3a08:/tmp/nanosw04# 
```

今回スイッチプログラムに変更はないので、nanosw03 を再び実行し、PacketIn() 関数を呼び出して下さい。

```python
(venv) root@f4f19294589c:/tmp/nanosw04# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw03.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> PacketIn()

......
```

#### Mininet 側操作

ここで再び ping 要求を送ると、先ほど同様に ping 応答が帰ってくることが確認できます。

```bash
mininet> h1 ping h2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=8.38 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.701 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.778 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=1.13 ms
^C
--- 10.0.0.2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3055ms
rtt min/avg/max/mdev = 0.535/0.772/1.114/0.221 ms
mininet> 
```
#### P4 RuntimeShell 側画面
このとき、以下のような表示が出ていることが確認できます。最初の二つのパケットまでが Packet-In でコントローラに戻されており、二つ目の Packet-In 処理でフロー・エントリが設定されて以降はコントローラに Packet-In されることがなくなっています。
```bash
P4Runtime sh >>> PacketIn()

........
======              <<<< 一つ目のパケットの処理
packet-in: dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=1
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
.
======              <<<< 二つ目のパケットの処理
packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2
## INSERT ## dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=1
## INSERT ## dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=2
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:02 - port(2)
. 　　　　　
......^C  <<<< それ以降の ping のパケットは Packet-In されない（Control-C で中断）
Nothing (returned None)

P4Runtime sh >>> 

<<<< 必要なら以下のようにして l2_match_table に登録されたフロー・エントリを確認することもできる。
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01"
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x02"
  }
}
action {
  action {
    action_id: 16838673 ("MyIngress.forward")
    params {
      param_id: 1 ("port")
      value: "\\x00\\x01"
    }
  }
}

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

P4Runtime sh >>>
```
### パケットの往復とフロー・テーブルの内容

以下、少し細かくパケットの往復と、内部の処理について説明します。

この処理を実現するために、コントローラ側ではホストの MAC アドレスと、それが接続されたポート番号のテーブル（変数名 macTable）を維持しています。これをホスト・テーブルと呼びます。スイッチ側のテーブル、l2_match_table をフロー・テーブルと呼ぶことにします。

まずはじめに、二つのテーブルのステップごとの状態について図示しておきます。
<img src="../experiment.png" alt="attach:(Packet and flow entry sequences)" title="Packet and flow entry sequences">
以下にその詳細を説明します。

#### 1. Initial State

初期状態ではホスト・テーブル、フロー・テーブルともに空です。
```python
macTable = {}
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
|         |         |      |

#### 2. h1 -> h2 : ICMP Echo Request

最初のパケットはフロー・テーブルのマッチパターンに一致しないため、Packet-In されます。これを受け取ったコントローラは、以下の処理を行います。
1. 送信元である h1 のアドレスは"Unknown" つまりホスト・テーブルに無いため、ingress port である port 1 とともにホスト・テーブルに記録します。
2. 宛先 である h2 のアドレスも"Unknown" であるため、何もできることはありません。
3. このパケットはFlooding 指定をつけて Packet-Out します。
```python
macTable = { "00:00:00:00:00:01": 1 }
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
|         |         |      |

#### 3. h2 -> h1 : ICMP Echo reply

Floodingによって Echo Request が h2 に届き、h2 は h1 向けの返信を送ります。しかしこのパケットもフロー・テーブルのマッチパターンに一致しないため、Packet-In されます。これを受け取ったコントローラは、以下の処理を行います。
1. 送信元である h2 は"Unknown" であるため、ingress port である port 2 とともにホスト・テーブルに記録します。
3. 宛先である h1 は"Already known" つまりホスト・テーブルに既に存在しており、port 1 に送れば良いことが明らかです。宛先・送信元の情報が揃ったので、フロー・テーブルに往復ぶんのエントリを追加します。
4. このパケットは port 1 に向けて Packet-Out します。 

```python
macTable = { "00:00:00:00:00:01": 1,
             "00:00:00:00:00:02": 2 }
```
| dstAddr | srcAddr | port |
| ------- | ------- | ---- |
| 00:00:00:00:00:01 | 00:00:00:00:00:02 | 1 |
| 00:00:00:00:00:02 | 00:00:00:00:00:01 | 2 |

#### 4. after that....

これ以降に送られる h1 - h2 間の通信は、すべてコントローラを介さず、スイッチだけで転送されます。Packet-In や Flooding は一切生じません。



### 関係するコード

今回は Tutorial 3 のものと全く同じ nanosw03.p4 スイッチプログラムを使っています。Tutorial 3 との違いはコントローラ側、つまり shell.py だけです。

#### shell.py

今回のバージョンで最も重要な役割を果たしている packetin_process() 関数を以下に示します。すぐ上で説明した、h1, h2 間のパケットの往復と、それに対応する内部の処理が実現されています。

```python
def packetin_process(pin):
    payload = pin.packet.payload
    dstMac = payload[0:6]
    srcMac = payload[6:12]
    port = metadata_value(pin.packet.metadata, "packet_in", "ingress_port") # original ingres_port
    print("\n======\npacket-in: dst={0} src={1} port={2}"
            .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port, byteorder='big')))

    # if the source is new, record it with ingress port
    if srcMac not in macTable:
        macTable[ srcMac ] = port
    # when destnation is broadcast, no need to record it
    if dstMac == b'\xff\xff\xff\xff\xff\xff':
        print("broadcast!")
    else:
        if dstMac in macTable: # if the destination is recorderd, set entry
            insertFlowEntry(dstMac, srcMac, macTable[ dstMac ])
            insertFlowEntry(srcMac, dstMac, macTable[ srcMac ])
            # send to appropriate port
            port = macTable[ dstMac ]
            mcast_grp = b'\x00' # no Multicast
        else:
            # send to all (except original ingress port)
            mcast_grp = FLOOD_GRP 
        # Packet-out (as single-out or flood) 
        PacketOut(port, mcast_grp, payload)

```

上の packetin_process() 関数から呼び出される insertFlowEntry() 関数も shell.py 中にあります。

```python
def insertFlowEntry(dstMac, srcMac, port):
    print("## INSERT ## dst={0} src={1} port={2}" 
            .format(mac2str(dstMac), mac2str(srcMac), int.from_bytes(port, byteorder='big')))

    req = p4runtime_pb2.WriteRequest()
    update = req.updates.add()
    update.type = p4runtime_pb2.Update.INSERT

    table_entry = update.entity.table_entry
    table_entry.table_id = context.get_obj_id(P4Type.table, "MyIngress.l2_match_table") # 33609159 
    m1 = p4runtime_pb2.FieldMatch()
    m1.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.dstAddr") # 1 
    m1.exact.value = dstMac
    m2 = p4runtime_pb2.FieldMatch()
    m2.field_id = context.get_mf_id("MyIngress.l2_match_table", "hdr.ethernet.srcAddr") # 2
    m2.exact.value = srcMac
    table_entry.match.append(m1)
    table_entry.match.append(m2)

    action = table_entry.action.action
    action.action_id = context.get_obj_id(P4Type.action, "MyIngress.forward") # 16838673 
    param = p4runtime_pb2.Action.Param()    
    param.param_id = context.get_param_id("MyIngress.forward", "port") # 1
    param.value = port 
    action.params.append(param)

    client.write(req)
```



#### context.py

ところで Tutorial 3 までは P4Runtime のメッセージに与える P4 Entitiy を、直接 id 番号で指定していました。この Tutorial では context.get_obj_id() 関数や context.get_mf_id() 関数などを使って名前からテーブル名やフィールド名の id 番号を得るようにしました。これらの関数は context.py で定義されています。

またcontroller packet metadata を扱うための関数群が含まれていなかったので、それらについてもcontext.py に追加しています。packetin_process() 関数から呼び出される metadata_value() 関数などで使われています。



これで一連のチュートリアルが完了しました。お疲れさまでした。

## Next Step

次は[ここ](README.md#next-step)でしょうか。
