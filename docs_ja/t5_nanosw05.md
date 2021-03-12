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

$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```

#### P4Runtime Shell 側操作

一旦 P4Runtime Shell の実行を終わり、機能追加された shell.py と置き換えます。

```python
P4Runtime sh >>> exit
(venv) root@1923f14d3a08:/tmp/nanosw03# cd ../nanosw05
(venv) root@1923f14d3a08:/tmp/nanosw05# cp shell.py /p4runtime-sh/p4runtime_sh/shell.py 
(venv) root@1923f14d3a08:/tmp/nanosw05# cp context.py /p4runtime-sh/p4runtime_sh/context.py 
(venv) root@1923f14d3a08:/tmp/nanosw05# 
```

今回はスイッチプログラムに変更を加えています。nanosw05 を実行し、PacketIn() 関数を呼び出して下さい。

```python
(venv) root@f4f19294589c:/tmp/nanosw05# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw04.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> PacketIn()

......
```

#### 再び Mininet 側操作

ここで再び ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。

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
```
以下のようにして l2_match_table に登録されたフロー・エントリを確認することもできます。このタイミングではテーブルには三つのエントリが登録されているはずです。一つめがブロードキャストを flooding するためもので、残りの二つが h1, h2 間のパケット往復について forward するためのエントリーです。

```bash
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))    
            ...:                                                                                                                                                                                                    
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\xff\\xff\\xff\\xff\\xff\\xff" <<< 宛先がブロードキャストで
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01" <<< 送信元が h1
  }
}
action {
  action {
    action_id: 16837454 ("MyIngress.flooding")  <<<< action に flooding が設定されている
  }
}

table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01" <<< 宛先が h1
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x02" <<< 送信元が h2
  }
}
action {
  action {
    action_id: 16838673 ("MyIngress.forward") <<<< action は forward to port 1
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
    value: "\\x00\\x00\\x00\\x00\\x00\\x02" <<< 宛先が h2
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x00\\x00\\x00\\x00\\x00\\x01" <<< 送信元が h1
  }
}
action {
  action {
    action_id: 16838673 ("MyIngress.forward") <<<< action は forward to port 2
    params {
      param_id: 1 ("port")
      value: "\\x00\\x02"
    }
  }
}

<<<< 以下のようにテーブルの中身を削除してから、もう一度挙動を見ると良い。
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: a.delete())                                                                                                          

```


### パケットの往復とフロー・テーブルの操作

以下、h1 から h2 に対して ping したときに生じるパケットの往復と、内部の処理について説明します。

1. h1から ARP request が出る
2. スイッチはこれをコントローラに packet in する
3. コントローラは宛先をブロードキャスト、送信元が h1 のマッチパターンと、action flodding をフロー・エントリに登録する
4. コントローラは受け取ったパケットを flooding （受け取ったポート以外に packet out）する
5. この 4. によって転送された ARP パケットを h2 が受け取り、これに reply を出す
6. やはりこのパターンはフロー・エントリにないので、コントローラに packet-in する
7. コントローラは宛先 h1、送信元 h2 のパターンを action forward として登録する
8. コントローラは受け取ったパケットを flooding （受け取ったポート以外に packet out）する

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

#### shell.py

この、action flooding をセットする処理は先ほど置き換えた shell.py の中の幾つかの関数に実装されています。以下に主要な部分だけ抜粋して示します。まず PacketIn() 関数関連。

```Python
FLOOD_PORT = b'\xff\xff'
def packetin_process(pin):
    payload = pin.packet.payload
    port = pin.packet.metadata[0].value   # original ingres_port
    payload = pin.packet.payload
    if dstMac == b'\xff\xff\xff\xff\xff\xff':
        print("broadcast!")
        if srcMac not in macTable:
            macTable[ srcMac ] = port
        insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
        PacketOut(port, FLOOD_GRP, payload)
    else: # when destination is unicast, do forwarding
        # if the source is new, record it with ingress port
        if srcMac not in macTable:
            macTable[ srcMac ] = port
        if dstMac in macTable: # if the destination is recorderd, set entry
            insertFlowEntry(dstMac, srcMac, macTable[ dstMac ])
            insertFlowEntry(srcMac, dstMac, macTable[ srcMac ])
            # send to appropriate port
            port = macTable[ dstMac ]
            mcast_grp = b'\x00\x00' # no Multicast
        else:
            # send to all (except original ingress port)
            mcast_grp = FLOOD_GRP 
        # Packet-out (as single-out or flood) 
        PacketOut(port, mcast_grp, payload)

def insertFlowEntry(dstMac, srcMac, port):
    (...snip...)
    if port is FLOOD_PORT: # set action to flooding 
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

つまりpacketin_process() 関数が、受け取ったパケットがブロードキャストであれば、ポート番号を（Floodingすべき処理の目印である）FLOOD_PORT として insertFlowEntry() を呼び出します。そこではポート番号がFLOOD_PORTであれば、action として flooding をつけてフロー・エントリをセットします。もしブロードキャストででなければポート番号は入力ポートとなり、insertFlowEntry() 内では、action として forward をつけてフロー・エントリをセットします。

いずれにせよ、宛先ホストが存在するポートが判明していた場合は Unicast の指定と、当該ポートの情報をつけて。そうで無い場合（ブロードキャストあるいは宛先ホストのポート不明）はMulticast Group の情報(1) と、元の Ingress_port の情報をつけて、PacketOut() 関数を呼び出します。

#### エントリ設定前後での ping 処理時間

ここで再び ping 要求を送ると、先ほど同様に ping 応答が帰ってくることが確認できます。ただ、今度はパケットはスイッチに設定されたフロー・エントリに従って折り返され、コントローラに送られてくることはありません。

その応答時間に注目してください。つまり今回はMininet上のホストは ARP パケットを出しません。コントローラ側でのフロー・エントリの設定や Packet Out による転送処理も無し。スイッチだけで高速に処理が完了していることを確認できるでしょう。私の手元の環境では初回が 9ms 程度掛かるのに対して、それ以降は 1ms 以下で完了します。

```bash
mininet> h1 ping -c 1 h2 
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.783 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.783/0.783/0.783/0.000 ms
mininet> 
```



これで一連のチュートリアルが完了しました。お疲れさまでした。

## Next Step

次は[ここ](README.md#next-step)でしょうか。
