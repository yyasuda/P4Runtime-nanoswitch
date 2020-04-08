## RAW パケットを送信する方法

Mininet では ping などのツールがあり、ARP などを生じさせずに簡単にパケットを送信できますが、たとえば Wedge Switch など実機を使った実験などでは、Wedge 自身 (OpenNetworkLinux) あるいは Wedge のポートに接続した Mac などから任意のパケットを送信したくなるでしょう。そうした場合のツールを置いておきます。

### rawsend.py - for Linux

Linux 環境では、このチュートリアルに含まれている rawsend.py が使えます。

```python
import socket
iface = 's1-eth1'
dstMac = b'\x01\x01\x01\x01\x01\x01'
srcMac = b'\x02\x02\x02\x02\x02\x02'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
s.send(packet)
print('Packet sent.')
s.close()
```

実行は単に ```python rawsend.py``` とするだけで良いのですが、以下のようにすれば Mininet 環境でも簡単に使うことができます。

```python
mininet> sh cat > rawsend.py
import socket
iface = 's1-eth1'
dstMac = b'\x01\x01\x01\x01\x01\x01'
srcMac = b'\x02\x02\x02\x02\x02\x02'
proto = b'\x88\xb5' # protocol type is IEEE Local Experimental
packet = dstMac + srcMac + proto + "012345678901234567890123456789012345678901234567890123456789"
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) # 3:ETH_P_ALL
s.bind((iface, 0))
s.send('Packet sent.')
print(packet)
s.close()
mininet> sh python rawsend.py
Packet sent.
mininet> 
```

モニタリング結果を出しておきます。

```bash
root@cc44475855d7:~#  tcpdump -XX -i s1-eth1
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on s1-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
04:00:37.407342 02:02:02:02:02:02 (oui Unknown) > 01:01:01:01:01:01 (oui Unknown), ethertype Unknown (0x88b5), length 74: 
	0x0000:  0101 0101 0101 0202 0202 0202 88b5 3031  ..............01
	0x0010:  3233 3435 3637 3839 3031 3233 3435 3637  2345678901234567
	0x0020:  3839 3031 3233 3435 3637 3839 3031 3233  8901234567890123
	0x0030:  3435 3637 3839 3031 3233 3435 3637 3839  4567890123456789
	0x0040:  3031 3233 3435 3637 3839                 0123456789
```



### rawsend.c - for MacOS

MacOS ではこのチュートリアルに含まれている rawsend.c が使えます。上の Python プログラムが使えれば簡単で良いのですが、AF_PACKET はLinux でしか使えず、BSD 系OSではBPF (Berkley Packet Filters) つまり pcap ライブラリを使って、以下のようにコードする必要があります。

```cc rawsend.c -lpcap``` などしてコンパイルして下さい。実行時には ```./a.out en0``` などとインタフェイスを指定してください。

```C
#include <stdlib.h> 
#include <stdio.h> 
#include <pcap.h>
int main(int argc, char **argv) {
    pcap_t *fp;
    char errbuf[PCAP_ERRBUF_SIZE]; 
    u_char packet[100];
    int i;

    /* Check the validity of the command line */
    if (argc != 2){
        printf("usage: %s interface", argv[0]); return 1;
    }
    /* Open the adapter */
    if ((fp = pcap_open_live(
            argv[1], // name of the device
            65536, // portion of the packet to capture. It doesn’t matter in this case 
            1, // promiscuous mode (nonzero means promiscuous)
            1000, // read timeout
            errbuf // error buffer
            )) == NULL) {
        fprintf(stderr,"\nUnable to open the adapter. %s is not supported\n", argv[1]);
        return 2;
    }
    // Setting dstMac to 01:01:01:01:01:01
    for(i = 0; i < 6; i++) packet[i]=0x01;
    // Setting srcMac to 02:02:02:02:02:02
    for(i = 0; i < 6; i++) packet[6+i]=0x02;
    // Fill the rest of the packet with data
    packet[12]=0x88; packet[13]=0xb5; // protocol type is IEEE Local Experimental
    // Fill the rest of the packet with data
    for(i = 0; i < 60; i++) packet[14 + i]= (u_char)('0' + (i % 10));

    // Send packet
    if (pcap_sendpacket(fp, packet, 6 + 6 + 2 + 60) != 0) {
        fprintf(stderr,"\nError sending the packet: %s\n", pcap_geterr(fp)); return 1;
    }
    printf("Packet sent.\n"); 
    pcap_close(fp);

    return 0;
}
```

source: https://tuprints.ulb.tu-darmstadt.de/6243/1/TR-18.pdf 

以下のようにしてコンパイル・実行すれば良いでしょう。

```bash
$ cc -o rawsend -lpcap rawsend.c
$

$ ./rawsend en0
Packet sent.
$
```

