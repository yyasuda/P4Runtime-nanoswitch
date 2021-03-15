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

#### P4Runtime Shell dev 版の作成と起動

このチュートリアルでの実験には、[p4runtime shell](https://github.com/p4lang/p4runtime-shell) Docker Image を、Dockerfile.dev を使ってビルドしたものを使用します。

```bash
$ git clone https://github.com/p4lang/p4runtime-shell.git
Cloning into 'p4runtime-shell'...
remote: Enumerating objects: 50, done.
(snip...)
Resolving deltas: 100% (101/101), done.
$ cd p4runtime-shell/
$ docker build -t myproj/p4rt-sh-dev -f Dockerfile.dev .
Sending build context to Docker daemon  372.2kB
Step 1/7 : FROM p4lang/p4runtime-sh:latest
(snip...)
Successfully built 5ddb6ed47ba8
Successfully tagged myproj/p4rt-sh-dev:latest
$ docker images
REPOSITORY            TAG                 IMAGE ID            CREATED             SIZE
myproj/p4rt-sh-dev    latest              5ddb6ed47ba8        23 seconds ago      285MB
```

ビルド出来たら、nanosw06 ディレクトリ以下を手元にコピーしてから、このようにして起動してください。

```bash
$ docker run -it -v /tmp/P4runtime-nanoswitch/nanosw06/:/tmp/ myproj/p4rt-sh-dev /bin/bash
root@9f0bcd94e736:/p4runtime-sh# source $VENV/bin/activate
(venv) root@9f0bcd94e736:/p4runtime-sh# cd /tmp
(venv) root@9f0bcd94e736:/tmp# ls
context.py  double_send.py  nanosw05.json  nanosw05.p4  nanosw05.p4i  p4info.txt  shell.py
(venv) root@9f0bcd94e736:/tmp# cp context.py shell.py /p4runtime-sh/p4runtime_sh/
(venv) root@9f0bcd94e736:/tmp# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XXX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,nanosw05.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>> me = MulticastGroupEntry(1).add(1).add(2).add(3)

P4Runtime sh >>> me.insert()

P4Runtime sh >>> PacketIn()

```

PacketIn() 後に、特に何もパケットを送っていないのに 33:33:00:00:00:02 宛てのパケットが幾つも目撃されるでしょうが、無視してください。

#### Mininet 側操作

ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。

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
P4Runtime sh >>> PacketIn()

........
======
packet-in: dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=1  <<<< ARP Request の Packet In
broadcast!
## INSERT ## dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 port=65535
  ## set flooding action
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:03 - port(3)
.
======
packet-in: dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=2  <<<< ARP Response の Packet In
## INSERT ## dst=00:00:00:00:00:01 src=00:00:00:00:00:02 port=1
## INSERT ## dst=00:00:00:00:00:02 src=00:00:00:00:00:01 port=2
macTable (mac - port)
 00:00:00:00:00:02 - port(2)
 00:00:00:00:00:01 - port(1)
 00:00:00:00:00:03 - port(3)
.....
......  
```

#### Mininet 側操作

もう一度 ping 要求を送ると、正しく ping 応答が帰ってくることが確認できます。このとき、P4Runtime Shell 側には Packet-In によるメッセージが出ず、パケットがコントローラを介さず、スイッチで折り返されたことが分かります。それだけでなく（ARP処理が不要なことと合わせて）応答時間が 10 倍ほど早くなっています。

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
......^C  <<<< Control-C で中断
Nothing (returned None)

P4Runtime sh >>> PrintTable()                                                                                         
MyIngress.l2_match_table
  dst=ff:ff:ff:ff:ff:ff src=00:00:00:00:00:01 action=MyIngress.flooding
  dst=00:00:00:00:00:01 src=00:00:00:00:00:02 action=MyIngress.forward ( 1 )
  dst=00:00:00:00:00:02 src=00:00:00:00:00:01 action=MyIngress.forward ( 2 )

P4Runtime sh >>>
```

さらにパケットの送受信を続けたい場合は PacketIn() 関数を再び実行してください。



