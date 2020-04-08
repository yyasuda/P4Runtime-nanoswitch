/*
    source is 
    A.4 sendpack c, "Introduction to RAW-sockets", 
    Jens Heuschkel, Tobias Hofmann, Thorsten Hollstein, Joel Kuepper,
    Technische Universität Darmstadt, 
    16.05.2017, Technical Report No. TUD­CS­2017­0111 
    https://tuprints.ulb.tu-darmstadt.de/6243/1/TR-18.pdf 
*/
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
