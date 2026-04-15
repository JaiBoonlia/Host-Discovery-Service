from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
import time

log = core.getLogger()

# ================================
# Host Registry + Switch Tables
# ================================
active_hosts = {}              # mac -> host info
host_port_map = {}             # dpid -> {mac: port}


def print_hosts():
    if not active_hosts:
        log.info("[INFO] No active hosts")
        return

    log.info("=" * 60)
    log.info(" ACTIVE HOST TABLE ")
    log.info("=" * 60)

    for mac, data in active_hosts.items():
        ts = time.strftime('%H:%M:%S', time.localtime(data['last_seen']))
        log.info("MAC=%s | IP=%s | SW=%s | PORT=%s | TIME=%s"
                 % (mac, data['ip'], data['dpid'], data['port'], ts))

    log.info("=" * 60)


def cleanup_hosts(timeout=60):
    now = time.time()
    for mac in list(active_hosts):
        if now - active_hosts[mac]['last_seen'] > timeout:
            del active_hosts[mac]
            log.info("[CLEANUP] Removed inactive host %s" % mac)


class DiscoveryController(EventMixin):

    def __init__(self, connection, dpid):
        self.connection = connection
        self.dpid = dpid_to_str(dpid)
        self.listenTo(connection)

        log.info("[SWITCH UP] %s connected" % self.dpid)

    def _handle_PacketIn(self, event):

        packet = event.parsed
        src = packet.src
        dst = packet.dst
        in_port = event.port
        dpid = self.dpid

        # Initialize switch table
        if dpid not in host_port_map:
            host_port_map[dpid] = {}

        # Learn MAC -> port
        host_port_map[dpid][src] = in_port

        # Extract IP
        ip_addr = "N/A"
        try:
            if packet.type == packet.ARP_TYPE:
                arp = packet.payload
                if str(arp.protosrc) != "0.0.0.0":
                    ip_addr = str(arp.protosrc)

            elif packet.type == packet.IP_TYPE:
                ip_addr = str(packet.payload.srcip)

        except:
            pass

        # Host detection
        prev = active_hosts.get(src)

        if (prev is None or
            prev['port'] != in_port or
            prev['dpid'] != dpid):

            active_hosts[src] = {
                'ip': ip_addr,
                'dpid': dpid,
                'port': in_port,
                'last_seen': time.time()
            }

            if prev is None:
                log.info("[DISCOVERY] New host %s at %s (port %d)" % (src, dpid, in_port))
            else:
                log.info("[UPDATE] Host moved %s -> %s:%d" % (src, dpid, in_port))

            print_hosts()

        else:
            # just refresh timestamp
            active_hosts[src]['last_seen'] = time.time()

        # Cleanup old hosts
        cleanup_hosts()

        # Forwarding logic
        if dst in host_port_map.get(dpid, {}):
            out_port = host_port_map[dpid][dst]

            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.idle_timeout = 15
            msg.hard_timeout = 45
            msg.priority = 20
            msg.actions.append(of.ofp_action_output(port=out_port))
            msg.data = event.ofp

            self.connection.send(msg)

            log.debug("[FLOW] %s -> %s via %d" % (src, dst, out_port))

        else:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = in_port

            self.connection.send(msg)

            log.debug("[FLOOD] %s unknown" % dst)

    def _handle_ConnectionDown(self, event):
        log.info("[SWITCH DOWN] %s disconnected" % self.dpid)

        if self.dpid in host_port_map:
            del host_port_map[self.dpid]


class DiscoveryService(EventMixin):

    def __init__(self):
        self.listenTo(core.openflow)
        log.info("[INIT] Discovery Service started")

    def _handle_ConnectionUp(self, event):
        DiscoveryController(event.connection, event.dpid)


def launch():
    core.registerNew(DiscoveryService)
    log.info("[READY] Controller running")
