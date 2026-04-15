#!/usr/bin/env python3

"""
SDN Host Discovery - Custom Mininet Topology

Layout:
    Three hosts connected to first switch
    Two hosts connected to second switch
    Switches interconnected

Controller: Remote (127.0.0.1:6633)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class CustomNetwork(Topo):

    def build(self):

        # ----- switches -----
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')

        # ----- hosts -----
        hosts_s1 = [
            self.addHost('h1', ip='10.0.0.1/24'),
            self.addHost('h2', ip='10.0.0.2/24'),
            self.addHost('h3', ip='10.0.0.3/24')
        ]

        hosts_s2 = [
            self.addHost('h4', ip='10.0.0.4/24'),
            self.addHost('h5', ip='10.0.0.5/24')
        ]

        # ----- connections -----
        for h in hosts_s1:
            self.addLink(h, switch1)

        for h in hosts_s2:
            self.addLink(h, switch2)

        # inter-switch link
        self.addLink(switch1, switch2)


def start_network():

    setLogLevel('info')

    topo = CustomNetwork()

    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(
            name,
            ip='127.0.0.1',
            port=6633
        ),
        switch=OVSSwitch,
        autoSetMacs=True
    )

    net.start()

    info("\n[INFO] Network initialized\n")
    info("[INFO] Hosts ready: h1-h5\n")
    info("[INFO] Use 'pingall' to trigger controller learning\n\n")

    CLI(net)

    net.stop()


if __name__ == '__main__':
    start_network()
