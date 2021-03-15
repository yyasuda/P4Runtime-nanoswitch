## Tutorial 6: NanoSwitch06

ブロードキャストアドレス、あるいは未知のアドレス宛てのパケットによって出た Packet-In に反応して、フロー・エントリが作成されるのには時間が掛かります。エントリができるより前に同じアドレス宛てのパケットがもう一つ送られてきた場合、コントローラは二度 INSERT しようとしてエラーを発生させてしまいます。典型的なケースは、あるホストから二つのブロードキャストパケットが連続して送られることでしょう。二つのホストに対するARP Requestが出てくるなど、普通にありそうな状況です。

対処方法は色々あり得るのですが、ここでは最も簡単な対処を施します。つまりフロー・エントリの追加に際して、二重登録になった場合は、そのエラーを無視するのです。

### 実験

#### double_send.py

以下にブロードキャストパケットを二つ連続して送出する Python コードを示します。コード中の sleep() 時間を調整することで、どのくらいの時間でフロー・エントリのセットが完了するのか調べることもできるようにしています。送出先インタフェイスと srcMac を見ると分かるように、このプログラムは h1 ホストから送出された場合と等価なパケットを作ります。

```python
import socket
import time
iface = 'h1-eth0'
dstMac = b'\xff\xff\xff\xff\xff\xff'
srcMac = b'\x00\x00\x00\x00\x00\x01'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
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

nanosw05のチュートリアルに従って、同じ環境で Mininet / P4Runtime Shell を実行してください。そこで上のプログラムをMininet環境の /root 以下に置き、以下のようにして実行します。

```bash
mininet> h1 python double_send.py
send #1 packet. <<< この表示が出た後に 1 秒の待ち時間がある
send #2 packet.
done.
mininet> 
```

このパケットがただしく他のホスト、つまり h2, h3 に転送されていることを確認するには、h2 あるいは h3 側でモニタリングする必要があります。（モニタリング操作については [NanoSwitch01](t1_nanosw01.md) を参照してください。）

#### P4 RuntimeShell 側画面

今回、スイッチプログラムには変更がないため、nanosw05.p4 をそのまま使います。

上のようにして double_send.py プログラムを実行したとき、以下のような表示が出ていることが確認できます。最初のパケットの到着によって、宛先がブロードキャスト、送信元が h1 （00:00:00:00:00:01）のマッチ・パターンをもつフロー・エントリが登録されました。1秒後に送られた二つ目のパケットについてはそれに従って処理されるため、Packet-In されません。h2, h3 のインタフェイスのモニタリングで、スイッチ内で折り返されたパケットを確認できるでしょう。

```bash
P4Runtime sh >>> PacketIn()                                                                                                                     
.......
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
......
```

#### double_send.py の修正

この状態で、double_send.py の中身を修正して、待ち時間なしに二つ目のパケットを送るようにします。つまり、以下のように sleep() の行をコメントアウトしてしまえば良いでしょう。

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
P4Runtime sh >>> PacketIn()

======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<< 1つ目のパケットが届いた
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action  <<<< ここでフロー・エントリに追加される
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
.
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<< 2つ目のパケットも届いた
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action  <<<< 再びフロー・エントリに追加しようとすると、以下のようにエラーが出る
---------------------------------------------------------------------------
P4RuntimeWriteException                   Traceback (most recent call last)
<ipython-input-1-9a9af7272159> in <module>
----> 1 PacketIn()

/p4runtime-sh/p4runtime_sh/shell.py in PacketIn()
   2427                 # print("\nResponse message is:")
   2428                 # print(rep)
-> 2429                 packetin_process(rep)
   2430                 # return rep # if you want to check the response, just return
   2431     except KeyboardInterrupt:

/p4runtime-sh/p4runtime_sh/shell.py in packetin_process(pin)
   2389         if srcMac not in macTable:
   2390             macTable[ srcMac ] = port
-> 2391         insertFlowEntry(dstMac, srcMac, FLOOD_PORT)
   2392         PacketOut(port, FLOOD_GRP, payload)
   2393     else: # when destination is unicast, do forwarding

/p4runtime-sh/p4runtime_sh/shell.py in insertFlowEntry(dstMac, srcMac, port)
   2351 
   2352     # print(req)
-> 2353     client.write(req)
   2354 
   2355 # macTable = [ mac: port ] - store mac and port of source host

/p4runtime-sh/p4runtime_sh/p4runtime.py in handle(*args, **kwargs)
    122             if e.code() != grpc.StatusCode.UNKNOWN:
    123                 raise e
--> 124             raise P4RuntimeWriteException(e) from None
    125     return handle
    126 

P4RuntimeWriteException: Error(s) during Write:
	* At index 0: ALREADY_EXISTS, 'Match entry exists, use MODIFY if you wish to change action'

```
念のためにフロー・エントリ内容を確認すると、正しくブロードキャストパケットを flooding する設定が登録されています。

```bash
P4Runtime sh >>> PrintTable()                                                                                         
MyIngress.l2_match_table
  dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 action=MyIngress.flooding

P4Runtime sh >>>                                                                                                        
```

つまり今回は、1つ目のパケットの Packet-In 処理によってこのエントリが登録されるより早く、2つ目のパケットがスイッチに届いています。すると、この2つ目のパケットも Packet-In され、まったく同じフロー・エントリが二重に登録する処理が走りますが、そのための write() 処理が失敗し、P4RuntimeWriteException 例外を発生させてしまったのです。

### エラー対応

対処方法は色々あり得るのですが、ここでは最も簡単な対処を施します。つまりフロー・エントリの追加に際して、二重登録になった場合は、そのエラーを無視するのです。

#### shell.py

エラーを起こすのは shell.py 内の insertFlowEntry() 関数です。以下の箇所を修正することにします。元は以下の一行でした。

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
            print("already exists. ignore this.")
        else:
            print(e)
            raise e
```
つまり単純に二重登録になったエラーについては（念のために）メッセージだけ出して、それを無視するのです。ALREADY_EXISTS エラー以外はそのままエラーとして raise します。
なおこのコード追加のために、以下の2行を shell.py 冒頭に追加しています。

```python
from p4runtime_sh.p4runtime import P4RuntimeWriteException
from google.rpc import status_pb2, code_pb2 
```

#### 修正後のP4Runtime Shell 側での表示

ではここで、修正を加えた shell.py （つまりこの nanosw06 ディレクトリにあるもの）を使って、P4Runtime Shell を再起動し、再び Mininet 側で double_send.py を実行してください。以下のような表示になり、二重登録が発生しているものの、プログラムは停止しないことが確認できます。

```bash
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<<< 1つ目のパケットが届いた
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action <<<< ここでフロー・エントリに追加される
macTable (mac - port)
 00:00:00:00:00:01 - port(1)

.
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<<< 2つ目のパケットが届いた
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action <<<< 再びフロー・エントリに追加しようとする
already exists. ignore this.   <<<<< 今度はエラーを検出しているが停止はしない
macTable (mac - port)
 00:00:00:00:00:01 - port(1)
.........
```

まだまだスイッチとしては未完成ですが、P4 ベースの、コントローラつきのスイッチとしてやるべきことは一応カバーできたのではないかと思います。



これで一連のチュートリアルが完了しました。お疲れさまでした。

## Next Step

次は[ここ](README.md#next-step)でしょうか。

