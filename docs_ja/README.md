# P4Runtime-NanoSwitch

A Simple L2 lerning switch development tutorial on P4Runtime

### はじめに

このチュートリアルは、P4Runtime の Packet-In/Out 機能を使って簡単なスイッチを構築するものです。P4Runtime Shell をベースとした、簡易なコントローラを試作するとともに、今後あなたが継続的に機能を拡張するのが容易な環境を提供します。



## This tutorial does…

このチュートリアルでは、以下の四つのことを試します。最終的には非常に簡素な MAC Learning Switch が出来上がります。

1. Multicast Group の設定と、それを利用した Flooding 処理
2. Packet-In 処理を利用した、コントローラへの処理依頼
3. Packet-Out 処理を利用した、スイッチのテーブルへのエントリ追加
4. そうした実験を行うための P4Runtime Shell への機能追加

これらの実験は、以下の環境で行います。

- コントローラ役には P4Runtime Shell を用いる
- スイッチ役には P4Runtime に対応した Mininet を用いる
- P4 コンパイルにはオープンソースの p4c を用いる



## Step by Step

以下に一つずつ手順を示します。順番に試していくのが良いでしょう。

### Tutorial 0: [実験環境の準備](./t0_prepare.md)

Mininetを起動し、そこにコントローラ代わりとなる、P4 Runtime Shell を接続させます。

### Tutorial 1: [NanoSwitch01](./t1_nanosw01.md)

届いたパケットのすべてを全ポートにリピートします
- Multicast Group を設定し、そこに出力する

### Tutorial 2: [NanoSwitch02](./t2_nanosw02.md)

Ingress port をリピートの対象としないよう工夫します
- Multicast されたパケットのうち、Ingress port と同じ番号のポートだったら drop する

### Tutorial 3: [NanoSwitch03](./t3_nanosw03.md)

スイッチ側にフロー・テーブルを作って未知のホストに対応します
- Unknown なものは Packet-In する
- Packet-In されたパケットは全ポートにリピートするよう Packet-Out する 

### Tutorial 4: [NanoSwitch04](./t4_nanosw04.md)

コントローラ側にホスト・テーブルを作って既知のホストに対応します
- 既知のホスト・ペアの通信についてはフローテーブルに往復ぶんのエントリを追加する
- これ以降はコントローラを介さず、スイッチだけで往復パケットの転送が行われる

### Tutorial 5: [NanoSwitch05](./t5_nanosw05.md)

nanosw04では無視していたブロードキャスト処理を追加します

- ブロードキャストが出たらフローテーブルに対応したエントリを追加する
- ARP に対応し、普通のスイッチらしい挙動をするようになる

### Tutorial 6: [NanoSwitch06](./t6_nanosw06.md)

フローテーブルへのエントリ追加が間に合わない場合にエラーになることに対応します

- 二重登録になった場合、そのエラーを無視する

## Next Step

今回作成した Switch は、P4Runtime を分かりやすく試せることを優先しています。そのため機能的にはかなり不完全で、ぱっと思いつくだけでも以下の問題などがあります。これらについては、あなた自身で追加してみてはどうでしょう。

- 実際のスイッチ運用の場面では、ホスト X を、同じスイッチの port 1 から port 2 に差し替えることがよく起きます。しかしこのスイッチはそのようなことを考慮しておらず、差し替えるとパケットが往復できなくなります。

- 登録できるエントリ数には限りがありますから、しばらくパケットが流れなかったフローエントリについては削除すべきです。

- そもそも通常の L2 Learning Switch では、destination host が何番ポートに居るかだけを記憶し、フローごとにエントリを記憶する必要がありません。しかしP4 でそれを実現するには、source MAC でマッチングするものと、destination MAC + port でマッチングするものの、二つのテーブルが必要です。二つのテーブルを順にマッチしていくスイッチを作ってみませんか？



## Appendix

### 改造版 P4Runtime Shell

今回のチュートリアルは P4Runtime Shell に機能を追加しながら行いました。私の手元で使っていた[改造版 P4Runtime Shell](https://github.com/yyasuda/p4runtime-shell) を公開しています。Dockerfile.dev をオリジナル・バージョンと見比べれば、どこを改造したか分かると思います。これを Tutorial0: [実験環境の準備](t0_prepare.md) で示した方法で作成した [Docker Image](https://hub.docker.com/r/yutakayasuda/p4runtime-shell-dev) も公開しています。

そこには今回のチュートリアルで利用した機能がすべて含まれている上に、ここでは紹介しなかった機能もあります。興味のある方は以下のリンクを見て下さい。

- [改造版 P4Runtime Shell に追加したその他の機能](ta_p4rt-sh-misc.md)

### RAW パケットの送信

Mininet では ping などのツールがあり、ARP などを生じさせずに簡単にパケットを送信できますが、たとえば Wedge Switch など実機を使った実験などでは、Wedge 自身 (OpenNetworkLinux) あるいは Wedge のポートに接続した Windows/Mac などから任意のパケットを送信したくなるでしょう。そうした場合のツールを置いておきます。

- [RAW パケットを送信する方法](ta_rawsend.md)

### CPU port の変更

CPU port の情報は nanoswXX.p4 の冒頭にあります。必要に応じて以下の記述を変更して再コンパイルしてください。

```C++
#define CPU_PORT 255
```

もしあなたが試そうとするスイッチの CPU port 番号が分からない場合は、[P4Runtime-CPUport-finder](https://github.com/yyasuda/P4Runtime-CPUport-finder) が役に立つかも知れません。

