## Tutorial 0: 実験環境の準備

実験に先だって、P4 スイッチプログラムのコンパイルが必要です。次にMininetを起動し、そこにコントローラ代わりとなる、P4 Runtime Shell を接続させます。

スイッチプログラムのコンパイルについては、以下のように P4Runtime 対応のオプションを与えて下さい。

```bash
root@f53fc79201b8:/tmp# p4c --target bmv2 --arch v1model --p4runtime-files p4info.txt nanosw01.p4 
root@f53fc79201b8:/tmp# ls
nanosw01.json  nanosw01.p4  nanosw01.p4i  p4info.txt
root@f53fc79201b8:/tmp# 
```

ここで生成した p4info.txt と nanosw01.json を使って、あとで P4Runtime Shell を起動することになります。

### Step 1. スイッチの準備（Mininet 環境の立ち上げ）

#### システム構成

今回実験する環境のシステム構成を示します。

<img src="/Volumes/yasuda/Documents/Private/memo/P4/P4runtime-nanoswitch/system.png" alt="attach:(system structure)" title="System Structure" width="500">

#### Mininet 環境の立ち上げ

ここでは [P4Runtime-enabled Mininet Docker Image](https://hub.docker.com/r/opennetworking/p4mn) をスイッチとして利用します。以下のようにして起動すると良いでしょう。

P4Runtimeに対応した Mininet 環境を、Docker環境で起動します。起動時に --arp と --mac オプションを指定して、ARP 処理無しに ping テストなどができるようにしてあることに注意してください。

```bash
$ docker run --privileged --rm -it -p 50001:50001 opennetworking/p4mn --arp --topo single,3 --mac
(snip...)
*** Starting CLI:
mininet> 
```
s1 の port 1 が h1 に、port 2 が h2に、port 3 が h3 に接続されていることが確認できます。
```bash
mininet> net
h1 h1-eth0:s1-eth1
h2 h2-eth0:s1-eth2
h3 h3-eth0:s1-eth3
s1 lo:  s1-eth1:h1-eth0 s1-eth2:h2-eth0 s1-eth3:h3-eth0
mininet> 
```
h1 がスイッチにつながれているインタフェイス h1-eth0 の MAC アドレスは  00:00:00:00:00:01です。同様に h2 が 00:00:00:00:00:02、h3 が 00:00:00:00:00:03 です。

### Step2. P4Runtime Shell と Mininet の接続

#### P4Runtime Shellの起動

このチュートリアルでの実験には、[改造した P4Runtime Shell](https://github.com/yyasuda/p4runtime-shell) を用います。[Docker Image](https://hub.docker.com/r/yutakayasuda/p4runtime-shell-dev) もあります。

```bash
Cecil(133)% docker run -it -v /tmp/P4runtime-nanoswitch/:/tmp/ yutakayasuda/p4runtime-shell-dev /bin/bash
root@d633c64bbb3c:/p4runtime-sh# . activate 
(venv) root@d633c64bbb3c:/p4runtime-sh# 
```
ここではホストの /tmp/P4runtime-nanoswitch ディレクトリと docker の /tmp を同期させていることに注意して下さい。それから、上の `. activate` 処理はすぐこの後の操作で重要なので忘れないように。

#### Mininet への接続

以下のようにして Mininet に接続します。IPアドレスは自身の環境に合わせて下さい。

```bash
(venv) root@d633c64bbb3c:/p4runtime-sh# cd /tmp/nanosw01
(venv) root@d633c64bbb3c:/tmp/nanosw01# /p4runtime-sh/p4runtime-sh --grpc-addr 192.168.XX.XX:50001 --device-id 1 --election-id 0,1 --config p4info.txt,ether_switch.json
*** Welcome to the IPython shell for P4Runtime ***
P4Runtime sh >>>
```



## Next Step

#### Tutorial 1: [NanoSwitch01](t1_nanosw01.md)

