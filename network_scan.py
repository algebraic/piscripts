#!/usr/bin/env python3
import scapy.all as scapy
import argparse
import socket

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', dest='target', help='Target IP Address/Adresses')
    options = parser.parse_args()

    if not options.target:
        # use localhost if target isn't specified
        options.target = "192.168.86.1/24"
        # or throw an error
        # parser.error("[-] Please specify an IP Address or Addresses, use --help for more info.")
    return options
  
def scan(ip):
    arp_req_frame = scapy.ARP(pdst = ip)
    broadcast_ether_frame = scapy.Ether(dst = "ff:ff:ff:ff:ff:ff")
    broadcast_ether_arp_req_frame = broadcast_ether_frame / arp_req_frame
    answered_list = scapy.srp(broadcast_ether_arp_req_frame, timeout = 1, verbose = False)[0]

    result = []
    for i in range(0,len(answered_list)):
        mac = answered_list[i][1].hwsrc
        if mac.lower().startswith("2c:aa:8e"):
            ip = answered_list[i][1].psrc
            client_dict = {"ip" : ip, "mac" : mac}
            result.append(client_dict)

    return result
  
def display_result(result):
    print("-----------------------------------\nIP Address\tMAC Address\n-----------------------------------")
    for i in result:
        print("{}\t{}".format(i["ip"], i["mac"]))
  

options = get_args()
scanned_output = scan(options.target)
display_result(scanned_output)