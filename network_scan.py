import scapy.all as scapy
import argparse
import socket

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', dest='target', help='Target IP Address/Adresses')
    options = parser.parse_args()

    #Check for errors i.e if the user does not specify the target IP Address
    #Quit the program if the argument is missing
    #While quitting also display an error message
    if not options.target:
        #Code to handle if interface is not specified
        parser.error("[-] Please specify an IP Address or Addresses, use --help for more info.")
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

# wyze devices:
# 192.168.86.21
# 192.168.86.26
# 192.168.86.35
# 192.168.86.46
# 192.168.86.66
# 192.168.86.72
# 192.168.86.83