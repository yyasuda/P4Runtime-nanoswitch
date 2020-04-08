## 改造版 P4Runtime Shell に追加したその他の機能

このチュートリアルでは P4Runtime Shell にいくつかの機能を追加して実験を行いました。そこで利用した shell.py, context.py ファイルには、チュートリアルの中では紹介しなかった機能も含まれています。ここに紹介しておきます。



### Packet Out 操作

Request() 関数を起動します。指定されたファイルからメッセージ内容を読み取り、これをP4RuntimeのStreamMessageRequest メッセージとしてスイッチに送り込みます。
特に戻り値やメッセージは返ってきません。画面上には送信するメッセージの内容がprintされます。

```bash
P4Runtime sh >>> Request("/tmp/packetout.txt")                                                                                             
packet {
  payload: "\377\377\377\377\377\377\377\377\377\377\377\377\000\0001234567890123456789012345678901234567890123456789012345678901234567890123456789"
  metadata {
    metadata_id: 1
    value: "\000\001"
  }
}

P4Runtime sh >>> 
```



### エントリ追加操作

Write() 関数によってWriteRequest メッセージをスイッチに送り込みます。その結果、往復のための 2 つのエントリがテーブルに登録されていることが確認出来るでしょう。

```bash
P4Runtime sh >>> Write("/tmp/h1_to_h2.txt")                                                                                                    

P4Runtime sh >>> table_entry["MyIngress.l2_match_table"].read(lambda a: print(a))                                                              
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
```



### Packet-In のモニタリング

Watch() 関数によって Packet-In (StreamMessageResponse) を見張ることができます。例えば以下のように Watch() 関数を実行すると、待ち受け状態になります。（3 秒で timeout します）

```bash
P4Runtime sh >>> res = Watch()
```

この状態で Mininet から ```h1 ping -c 1 h3``` などとしてパケットを送ると、Watch() 関数は受信したメッセージの内容を画面表示し、またそれを戻り値として返します。

```bash
P4Runtime sh >>> res = Watch()
Response message is:
packet {
  payload: "\000\000\000\000\000\003\000\000\000\000\000\001\010\000E\000\000T\247J@\000@\001\177[\n\000\000\001\n\000\000\003\010\000\306r\000\252\000\001\3366\215^\000\000\000\000\000z\006\000\000\000\000\000\020\021\022\023\024\025\026\027\030\031\032\033\034\035\036\037 !\"#$%&\'()*+,-./01234567"
  metadata {
    metadata_id: 1
    value: "\000\001"
  }
  metadata {
    metadata_id: 2
    value: "\000"
  }
}
```



