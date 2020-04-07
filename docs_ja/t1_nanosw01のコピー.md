## Tutorial 1: NanoSwitch01

まず最初に、最も簡単なスイッチとして、届いたパケットのすべてを全ポートにリピートするものを作ります。P4 では、そうした用途のために Multicast Group 機能が用意されています。

###  マルチキャストグループの設定

スイッチ s1 は port 1, 2, 3 の三つのポートを持っています。これらをすべて一つの Multicast Group に登録し、そこにパケットを出力することで、いわゆる Flooding が行われます。
```python
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)
P4Runtime sh >>> me.insert()
P4Runtime sh >>> me.read()   # 必要なら確認
```











### エントリ追加操作

Tutorial 3 同様に、P4Runtime Shell 側で Write() 関数によってWriteRequest メッセージをスイッチに送り込みます。その結果、往復のための 2 つのエントリが登録されていることが確認出来るでしょう。

```bash
P4Runtime sh >>> Write("/tmp/2to1.txt")

P4Runtime sh >>> table_entry["MyIngress.ether_addr_table"].read(lambda a: print(a))   
```
### ping 往復の確認
この往復のためのエントリ設定ができた状態で ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。（Tutorial 3 の状態では h1 から ping パケットが送信されてh2 に到達したとしても、その返信パケットがh1 に届かないために、ping コマンドは待ちぼうけになっていましたね。）
```bash
mininet> h1 ping -c 1 h2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.959 ms

--- 10.0.0.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.959/0.959/0.959/0.000 ms
mininet> 
```
このとき Packet-In が起きていないことを、Watch() 関数が何も受信せずタイムアウトする事によって確認出来ます。
```bash
P4Runtime sh >>> Watch()

None returned

P4Runtime sh >>>
```



これで一連のチュートリアルが完了しました。お疲れさまでした。

## Next Step

次は[ここ](README.md#next-step)でしょうか。
