## Tutorial 6: NanoSwitch06

ブロードキャストアドレス、あるいは未知のアドレス宛てのパケットによって出た Packet-In に反応して、フロー・エントリが作成されるのには時間が掛かります。エントリができるより前に同じアドレス宛てのパケットがもう一つ送られてきた場合、コントローラは二度 INSERT しようとしてエラーを発生させてしまいます。典型的なケースは、あるホストから二つのブロードキャストパケットが連続して送られることでしょう。二つのホストに対するARP Requestが出てくるなど、普通にありそうな状況です。

対処方法は色々あり得るのですが、ここでは最も簡単な対処を施します。つまりフロー・エントリの追加に際して、二重登録になった場合は、そのエラーを無視するのです。

### 実験

#### double_send.py

以下にブロードキャストパケットを二つ連続して送出する Python コード、double_send.py を示します。コード中の sleep() 時間を調整することで、どのくらいの時間でフロー・エントリのセットが完了するのか調べることもできるようにしています。送出先インタフェイスと srcMac を見ると分かるように、このプログラムは h1 ホストから送出された場合と等価なパケットを作ります。

```python
import socket
import time
iface = 'h1-eth0'
dstMac = b'\xff\xff\xff\xff\xff\xff'
srcMac = b'\x00\x00\x00\x00\x00\x01'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + b"012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
print('send #1 packet.')
s.send(packet)
time.sleep(1)
print('send #2 packet.')
s.send(packet)
print('done.')
s.close()
```

#### Mininet 側操作

Mininet からこのプログラムを実行するために、オプション ```-v /tmp/P4runtime-nanoswitch:/tmp``` をつけて Mininet を再起動すると良いでしょう。

```bash
$ docker run --privileged --rm -it -v /tmp/P4runtime-nanoswitch:/tmp -p 50001:50001 -e IPV6=false yutakayasuda/p4mn --topo single,3 --mac
```

P4Runtime Shell は nanosw05 のチュートリアルに従って、そのまま同じ nanosw05 のファイル群を使って再起動し、コントローラ・プログラムを同じように起動してください。

```bash
$ docker run -ti -v /tmp/P4runtime-nanoswitch:/tmp p4lang/p4runtime-sh --grpc-addr 192.168.1.2:50001 --device-id 1 --election-id 0,1 --config /tmp/nanosw05/p4info.txt,/tmp/nanosw05/nanosw05.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> import sys
P4Runtime sh >>> sys.path.append "/tmp/nanosw05"
P4Runtime sh >>> import tutorial
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)
P4Runtime sh >>> me.insert()
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```

この状態で、double_send.py を以下のようにして実行します。

```bash
mininet> h1 pwd
/tmp
mininet> h1 python double_send.py
send #1 packet. <<< この表示が出た後に 1 秒の待ち時間がある
send #2 packet.
done.
mininet> 
```

このパケットがただしく他のホスト、つまり h2, h3 に転送されていることを確認するには、h2 あるいは h3 側でモニタリングする必要があります。（モニタリング操作については [NanoSwitch01](t1_nanosw01.md) を参照してください。）

#### P4 RuntimeShell 側画面

上のようにして double_send.py プログラムを実行したとき、以下のような表示が出ていることが確認できます。最初のパケットの到着によって、宛先がブロードキャスト、送信元が h1 （00:00:00:00:00:01）のマッチ・パターンをもつフロー・エントリが登録されました。1秒後に送られた二つ目のパケットについてはそれに従って処理されるため、Packet-In されません。h2, h3 のインタフェイスのモニタリングで、スイッチ内で折り返されたパケットを確認できるでしょう。

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action
send 
 payload: "\\xff\\xff\\xff\\xff\\xff\\xff\\x00\\x00\\x00\\x00\\x00\\x01\\x88\\xb5\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39\\x30\\x31\\x32\\x33\\x34\\x35\\x36\\x37\\x38\\x39"
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
```

#### double_send.py の修正

ここで一旦コントローラ・プログラムを終了（Control-C で中断）し、テーブルのフロー・エントリを削除してから、コントローラ・プログラムを同じように実行します。

```python
^C    <<<< Control-C で中断
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: a.delete())

P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)
```

その後に、double_send.py の中身を修正して、待ち時間なしに二つ目のパケットを送るようにします。つまり、以下のように sleep() の行をコメントアウトしてしまえば良いでしょう。

```python
print('send #1 packet.')
s.send(packet)
# time.sleep(1)    <<<< コメントアウトする
print('send #2 packet.')
s.send(packet)
```

#### Mininet で再送信

これを用いて再び Mininet 側で送信操作をします。

```bash
mininet> h1 python double_send.py
send #1 packet. <<< 今度はここで待たない
send #2 packet.
done.
mininet> 
```

#### P4 RuntimeShell 側画面

今度は以下のようなエラーをだして、P4Runtime Shell が停止してしまうでしょう。

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action        <<<< ここでフロー・エントリに追加される
send 
....(snip)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action  <<<< 再びフロー・エントリに追加しようとすると、以下のようにエラーが出る
---------------------------------------------------------------------------
P4RuntimeWriteException                   Traceback (most recent call last)
<ipython-input-15-1d4a43dd2314> in <module>
----> 1 tutorial.controller_daemon(packet_in, tutorial.my_packetin)

/tmp/nanosw05/tutorial.py in controller_daemon(packet_in, my_packetin, args)
     86             try:
     87                 pin = packet_in.packet_in_queue.get(block=True)
---> 88                 my_packetin(pin)
     89             except KeyboardInterrupt:
     90                 break

/tmp/nanosw05/tutorial.py in my_packetin(pin)
     60         if srcMac not in macTable:
     61             macTable[srcMac] = port
---> 62         insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
     63         my_packetout(str(int.from_bytes(port,'big')), FLOOD_GRP, payload)
     64     else:  # unicast

/tmp/nanosw05/tutorial.py in insertFlowEntry(dstMac, srcMac, port)
     45         action.params.append(param)
     46 
---> 47     client.write(req)
     48 
     49 def my_packetin(pin):

/p4runtime-sh/venv/lib/python3.10/site-packages/p4runtime_sh/p4runtime.py in handle(*args, **kwargs)
    123             if e.code() != grpc.StatusCode.UNKNOWN:
    124                 raise e
--> 125             raise P4RuntimeWriteException(e) from None
    126     return handle
    127 

P4RuntimeWriteException: Error(s) during Write:
	* At index 0: ALREADY_EXISTS, 'Match entry exists, use MODIFY if you wish to change action'
```
念のためにフロー・エントリ内容を確認すると、正しくブロードキャストパケットを flooding する設定が登録されています。

```bash
P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda te: print(te))
table_id: 33609159 ("MyIngress.l2_match_table")
match {
  field_id: 1 ("hdr.ethernet.dstAddr")
  exact {
    value: "\\xff\\xff\\xff\\xff\\xff\\xff"
  }
}
match {
  field_id: 2 ("hdr.ethernet.srcAddr")
  exact {
    value: "\\x01"
  }
}
action {
  action {
    action_id: 16837454 ("MyIngress.flooding")
  }
}

P4Runtime sh >>>          
```

つまり今回は、1つ目のパケットの Packet-In 処理によってこのエントリが登録されるより早く、2つ目のパケットがスイッチに届いています。すると、この2つ目のパケットも Packet-In され、まったく同じフロー・エントリが二重に登録する処理が走りますが、そのための write() 処理が失敗し、P4RuntimeWriteException 例外を発生させてしまったのです。

### エラー対応

対処方法は色々あり得るのですが、ここでは最も簡単な対処を施します。つまりフロー・エントリの追加に際して、二重登録になった場合は、そのエラーを無視するのです。

#### tutorial.py

エラーを起こすのは tutorial.py 内の insertFlowEntry() 関数です。以下の箇所を修正することにします。元は以下の一行でした。

```python
def insertFlowEntry(dstMac, srcMac, port):
    ...(snip)...
    client.write(req)
```
ここに以下のようにエラーハンドリング処理を加えます。
```python
    try:
        client.write(req)
    except P4RuntimeWriteException as e:
        if e.errors[0][1].canonical_code == code_pb2.ALREADY_EXISTS:
            print("Flow already exists. ignoring.")
        else:
            print(e)
            raise e
```
つまり単純に二重登録になったエラーについては（念のために）メッセージだけ出して、それを無視するのです。ALREADY_EXISTS エラー以外はそのままエラーとして raise します。
なおこのコード追加のために、以下の2行を tutorial.py 冒頭に追加しています。

```python
from p4runtime_sh.p4runtime import P4RuntimeWriteException
from google.rpc import status_pb2, code_pb2 
```

#### 修正後のP4Runtime Shell 側での表示

ではここで、修正を加えた tutorial.py （つまりこの nanosw06 ディレクトリにあるもの）を使って、P4Runtime Shell を再起動し、再び Mininet 側で double_send.py を実行してください。以下のような表示になり、二重登録が発生しているものの、プログラムは停止しないことが確認できます。

```bash
P4Runtime sh >>> tutorial.controller_daemon(packet_in, tutorial.my_packetin)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action  <<<< ここでフロー・エントリに追加される
send 
...(snip)

packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
  ## set flooding action  <<<< 再びフロー・エントリに追加しようとする
Flow already exists. ignoring.   <<<<< 今度はエラーを検出しているが停止はしない
send 
...(snip)
```

まだまだスイッチとしては未完成ですが、P4 ベースの、コントローラつきのスイッチとしてやるべきことは一応カバーできたのではないかと思います。



これで一連のチュートリアルが完了しました。お疲れさまでした。

## Next Step

次は[ここ](README.md#next-step)でしょうか。

