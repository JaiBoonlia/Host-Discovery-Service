# Host Discovery Service using SDN (Mininet + POX)

---

## Overview

This project implements a Host Discovery Service in a Software Defined Networking (SDN) environment using Mininet as the network emulator and the POX controller for centralized network control. The controller dynamically detects hosts via `packet_in` events, maintains a live host database, and installs OpenFlow flow rules to enable efficient and scalable packet forwarding.

A two-switch, five-host topology is used to ensure cross-switch host discovery, exercise inter-switch communication, and demonstrate that the controller maintains a global network view across multiple datapaths.

---

## Objectives

- Dynamically detect and register hosts as they join the network  
- Maintain a real-time host database (MAC, IP, switch DPID, port, timestamp)  
- Implement learning switch behavior at the controller level  
- Install and verify OpenFlow flow rules for efficient forwarding  
- Demonstrate controller–switch interaction using Mininet  

---

## Network Topology

```
  h1 ─┐                    ┌─ h4
  h2 ─┼─── s1 ──────── s2 ─┼─ h5
  h3 ─┘                    └─────
```

| Component | Details |
|-----------|---------|
| Switches | s1, s2 |
| Hosts on s1 | h1, h2, h3 |
| Hosts on s2 | h4, h5 |
| Inter-switch link | s1 ↔ s2 |
| Controller | POX (OpenFlow 1.0) |

This topology ensures communication across switches and validates controller-driven forwarding decisions.

---

## Prerequisites

Install required packages (tested on Ubuntu 20.04+):

```bash
sudo apt-get install mininet python3 iperf -y
```

Required tools:
- Mininet (network emulator)  
- POX Controller (Python-based OpenFlow controller)  
- Open vSwitch (`ovs-ofctl`) for flow inspection  

Copy the controller file to POX:

```bash
cp host_discovery.py ~/pox/ext/
```

---

## Project Structure

```
.
├── host_discovery.py
├── topology.py
├── README.md
└── screenshots/
```

Screenshots include:
- Connectivity results  
- Controller logs  
- Flow table verification  
- Failure scenarios  
- Performance results  

---

## Setup and Execution

### Step 1 — Start Controller

```bash
cd ~/pox
./pox.py host_discovery
```

---

### Step 2 — Start Topology

```bash
sudo python3 topology.py
```

---

### Step 3 — Trigger Discovery

```
mininet> pingall
```

This generates traffic that triggers host discovery through `packet_in` events.

---

## SDN Logic and Flow Handling

### Workflow

```
Packet arrives at switch
        │
        ▼
Flow rule match? → YES → Forward
        │
        NO
        ▼
packet_in → Controller
        │
        ├─ Learn MAC and port
        ├─ Check destination
        │     ├─ Known → Install flow → Forward
        │     └─ Unknown → Flood
        ▼
Update host database
```

---

### Flow Rule Parameters

| Parameter | Value |
|----------|------|
| Match | MAC, IP, Input Port |
| Action | Output port |
| Priority | 10 |
| Idle Timeout | 20 seconds |
| Hard Timeout | 60 seconds |

---

## Scenario 1 — Full Connectivity

Command:
```
mininet> pingall
```

Result:
```
0% packet loss
```

All hosts are discovered and reachable. Initial packets trigger controller logic; subsequent packets are handled by switches.

---

## Scenario 2 — Failure Case

```
mininet> h2 ifconfig h2-eth0 down
mininet> h1 ping h2
```

Result:
- 100% packet loss  
- Flow rules expire after timeout  
- Network correctly reflects host failure  

---

## Scenario 3 — Flow Table Verification

```bash
sudo ovs-ofctl dump-flows s1
sudo ovs-ofctl dump-flows s2
```

Confirms:
- Flow rules installed  
- Packet counters increment  
- Forwarding handled in data plane  

---

## Scenario 4 — Host Database

All hosts are discovered with:
- MAC address  
- IP address  
- Switch ID  
- Port  
- Timestamp  

---

## Performance Observations

### Latency

- First packet: ~6 ms (controller involved)  
- Subsequent packets: ~0.1 ms (direct forwarding)  

This demonstrates reactive flow installation.

---

### Throughput

Using `iperf`:

- ~127 Gbps observed (expected in Mininet environment)  

Indicates maximum data-plane performance after rule installation.

---

### Summary

| Metric | First Packet | Subsequent |
|-------|------------|-----------|
| Latency | High | Low |
| Controller usage | Yes | No |
| Throughput | N/A | High |

---

## Validation

System tested for:
- Connectivity  
- Controller logging  
- Flow installation  
- Failure handling  
- Performance metrics  

All expected behaviors were observed.

---

## Conclusion

This project demonstrates a functional SDN-based host discovery system with:

- Separation of control and data planes  
- Reactive flow installation  
- Centralized network visibility  
- Efficient data-plane forwarding  

---

## References

- Mininet Documentation  
- POX Controller (noxrepo)  
- OpenFlow 1.0 Specification  
- Open vSwitch Documentation  
