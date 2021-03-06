from scapy.all import *
import argparse
from termcolor import colored


class CherryWasp:
    """ Cherry Wasp

        The object that inspects each packet and determines how to handle it

        1. scan_type is defined on the CLI by the user:
            a. Scan Type 0 = Beacons only
            b. Scan Type 1 = Probe Requests only
            c. Scan Type 2 = Beacon & Probe Requests

        2. self.access_points is a list of BSSIDs or MAC addresses of devices beaconing ESSIDs.
        3. self.clients is a list of BSSIDs or MAC addresses of devices that are sending probe requests.
    """

    def __init__(self, scan_type):
        self.scan_type = scan_type
        self.access_points = []  # TODO: convert to set
        self.access_points_bssids = []
        self.clients = []
        self.clients_bssids = []  # TODO: convert to set

    def scan_packet(self, pkt):
        if self.scan_type == '0' or self.scan_type == '2':
            if pkt.haslayer(Dot11Beacon):
                essid = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.info%}")
                bssid = pkt.sprintf("%Dot11.addr2%")
                no_broadcast = False
                if bssid not in self.access_points_bssids:
                    self.access_points_bssids.append(bssid)
                    # print self.access_points_bssids
                    new_ap = CherryAccessPoint(bssid)
                    # print "new AP object created"
                    self.access_points.append(new_ap)
                    # print self.access_points
                if essid != "":
                    no_broadcast = True
                if no_broadcast is True:
                    for access_point in self.access_points:
                        if bssid == access_point.bssid and essid not in access_point.beaconed_essid:
                            # print access_point.beaconed_essid
                            access_point.add_new_beaconded_essid(essid)
                            print "[+] <{0}> is beaconing as {1}".format(colored(access_point.bssid, 'red'),
                                                                         colored(essid, 'green'))
                            with open("beacon_essids.csv", "a") as b:
                                b.write("{0},{1}\n".format(access_point.bssid, essid))
        if self.scan_type == '1' or self.scan_type == '2':
            if pkt.haslayer(Dot11ProbeReq):
                essid = pkt.sprintf("{Dot11ProbeReq:%Dot11ProbeReq.info%}")
                bssid = pkt.sprintf("%Dot11.addr2%")
                no_broadcast = False
                if bssid not in self.clients_bssids:
                    self.clients_bssids.append(bssid)
                    # print self.clients_bssids
                    new_client = CherryClient(bssid)
                    # print "new client object"
                    self.clients.append(new_client)
                if essid != "":
                    no_broadcast = True
                if no_broadcast is True:
                    for client in self.clients:
                        if bssid == client.bssid and essid not in client.requested_essid:
                            # print client.requested_essid
                            client.add_new_requested_essid(essid)
                            print "[+] Probe Request for {0} from <{1}>".format(colored(essid, 'green'),
                                                                                colored(client.bssid, 'red'))
                            with open("probe_requests.csv", "a") as r:
                                r.write("{0},{1}\n".format(client.bssid, essid))


class CherryAccessPoint:
    """ Cherry Access Point:

        An object that represents an Access Point seen in the environment.

        1. Type defines it as an access point.
        2. BSSID is the MAC address of the access point.
        3. beaconed_essid is a list that holds all of the essids the MAC address has beaconed
        4. evil_access_point is False by default, but switches to True if it appear to beaconing too many ESSIDs

        add_new_essid adds a new ESSID or network name to the list for the particular client.
    """
    def __init__(self, bssid):
        self.type = "access_point"
        self.bssid = bssid
        self.beaconed_essid = []

    def add_new_beaconded_essid(self, new_essid):
        self.beaconed_essid.append(new_essid)


class CherryClient:
    """ Cherry Client
        An object that reprenets a wireless client seen in that environment.

        1. Type defines it as a client.
        2. BSSID is the MAC address of the client seen.
        3. requested_essid is all of the ESSIDs that the client has requested.

        add_new_essid adds a new ESSID or network name to the list for the particular client.
    """
    def __init__(self, bssid):
        self.type = "client"
        self.bssid = bssid
        self.requested_essid = []

    def add_new_requested_essid(self, new_essid):
        self.requested_essid.append(new_essid)


def main():
    parser = argparse.ArgumentParser(description='Scan for 802.11 Beacon and/or Probe Requests.')
    parser.add_argument('-m', '--mode', help='0=beacons, 1=probe requests, 2=both')
    parser.add_argument('-i', '--interface', help='specify interface to listen on')
    parser.add_argument('-b', '--bssid', help='specify bssid to filter <optional>')
    args = parser.parse_args()

    if args.interface is None:
        print "[!] must define an interface with <-i>!"
        print parser.usage
        exit(0)
    else:  # TODO: check interface for monitor mode
        conf.iface = args.interface

    try:
        scan_type = args.mode
        cherry_wasp = CherryWasp(scan_type)
    except Exception:
        raise

    # TODO: add threading
    if args.bssid is None:
        if args.mode is not None:
            sniff(prn=cherry_wasp.scan_packet)
        else:
            print "[!] invalid mode selected"
            print parser.usage
            exit(0)

    if args.bssid is not None:  # TODO: add BSSID input validation here
        if args.mode is "0":
            filter_bssid = str("ether src " + args.bssid)
            sniff(filter=filter_bssid, prn=cherry_wasp.scan_packet)
        else:
            print "[!] must use mode 0 when filtering by BSSID"
            exit(0)
    else:
        print "[!] must define a mode with <-m>!"
        print parser.usage
        exit(0)


if __name__ == "__main__":
    main()
