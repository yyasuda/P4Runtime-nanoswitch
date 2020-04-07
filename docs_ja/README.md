# P4Runtime-NanoSwitch

A Simple L2 lerning switch development tutorial on P4Runtime

### はじめに

このチュートリアルは、P4Runtime の Packet-In/Out 機能を使って簡単なスイッチを構築するものです。P4Runtime Shell をベースとした、簡易なコントローラを試作するとともに、今後あなたが継続的に機能を拡張するのが容易な環境を提供します。

## This tutorial does…

このチュートリアルでは、以下の三つのことを試します。最終的には非常に簡素な MAC Learning Switch が出来上がります。

1. Multicast Group の設定と、それを利用した Flooding 処理
2. Packet-In 処理を利用した、コントローラへの処理依頼
3. Packet-Out 処理を利用した、スイッチのテーブルへのエントリ追加

これらの実験は、以下の環境で行います。

- コントローラ役には P4Runtime Shell を用いる
- スイッチ役には P4Runtime に対応した Mininet を用いる
- P4 コンパイルにはオープンソースの p4c を用いる

### パケットの到来とフロー・エントリ作成の関係

今回作成する L2 Learning switch が、h1 から h2 へ ping したときに発生する、ping request / reply パケットが、どのようにフローテーブルを構成するのか、その過程を示します。

<img src="../experiment.png" alt="attach:(Packet and flow entry sequences)" title="Packet and flow entry sequences">



## Step by Step

以下に一つずつ手順を示します。順番に試していくのが良いでしょう。

### Tutorial 0: [実験環境の準備](./t0_prepare.md)

実験に先だって、P4 スイッチプログラムのコンパイルが必要です。次にMininetを起動し、そこにコントローラ代わりとなる、P4 Runtime Shell を接続させます。

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



## Next Step

今回作成した Switch は、P4Runtime を分かりやすく試せることを優先しています。そのため機能的にはかなり不完全で、ぱっと思いつくだけでも以下の問題などがあります。これらについては、あなた自身で追加してみてはどうでしょう。

- 未知のホスト X 宛てのパケットによって出た Packet-In に反応して、フロー・エントリが作成されるのには時間が掛かります。エントリができるより前に同じホスト X 宛てのパケットがもう一つ送られてきた場合、コントローラは二度 INSERT しようとしてエラーを発生させてしまいます。

- 実際のスイッチ運用の場面では、ホスト X を、同じスイッチの port 1 から port 2 に差し替えることがよく起きます。しかしこのスイッチはそのようなことを考慮しておらず、差し替えるとパケットが往復できなくなります。

- 登録できるエントリ数には限りがありますから、しばらくパケットが流れなかったフローエントリについては削除すべきです。

- そもそも通常の L2 Learning Switch では、destination host が何番ポートに居るかだけを記憶し、フローごとにエントリを記憶する必要がありません。しかしP4 でそれを実現するには、source MAC でマッチングするものと、destination MAC + port でマッチングするものの、二つのテーブルが必要です。二つのテーブルを順にマッチしていくスイッチを作ってみませんか？

  

### CPU port の変更

CPU port の情報は nanoswXX.p4 の冒頭にあります。必要に応じて以下の記述を変更して再コンパイルしてください。

```C++
#define CPU_PORT 255
```

もしあなたが試そうとするスイッチの CPU port 番号が分からない場合は、[P4Runtime-CPUport-finder](https://github.com/yyasuda/P4Runtime-CPUport-finder) が役に立つかも知れません。

