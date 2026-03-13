# AIGateway Interceptor - VPN Deployment Guide

> **Status:** This deployment model is planned for a future release.

## Overview

The VPN deployment model routes all client traffic through a VPN tunnel, where the AIGateway Interceptor transparently intercepts AI-bound requests without requiring per-client proxy configuration.

## Planned Architecture

```
┌──────────┐     VPN Tunnel      ┌─────────────────────────────┐
│  Client   ├───────────────────►│  VPN Gateway                │
│  Device   │  (WireGuard /      │  ┌───────────────────────┐  │
└──────────┘   OpenVPN)          │  │  iptables / nftables  │  │
                                 │  │  (redirect AI traffic) │  │
                                 │  └───────────┬───────────┘  │
                                 │              │               │
                                 │  ┌───────────▼───────────┐  │
                                 │  │  AIGateway Interceptor │  │
                                 │  │  (transparent mode)    │  │
                                 │  └───────────┬───────────┘  │
                                 │              │               │
                                 └──────────────┼───────────────┘
                                                │
                                         ┌──────▼──────┐
                                         │ AI Provider │
                                         │    APIs     │
                                         └─────────────┘
```

## Key Differences from On-Premise

| Aspect               | On-Premise (Current)           | VPN (Planned)                    |
|----------------------|--------------------------------|----------------------------------|
| Client configuration | HTTP proxy settings required   | VPN client only                  |
| Traffic routing      | Explicit proxy                 | Transparent via routing rules    |
| Certificate install  | Required on each client        | Pushed via VPN provisioning      |
| Scope                | Only proxy-configured apps     | All traffic from the device      |
| Deployment           | Docker Compose                 | Docker Compose + VPN server      |

## Planned Features

- WireGuard and OpenVPN support
- Automatic CA certificate distribution during VPN provisioning
- iptables rules to redirect AI provider traffic to mitmproxy in transparent mode
- Split tunneling: only AI-bound traffic goes through the interceptor
- Client provisioning scripts for macOS, Windows, and Linux

## Prerequisites (Planned)

- Dedicated server or VM with public IP (for VPN endpoint)
- WireGuard or OpenVPN installed
- AIGateway Interceptor stack (Docker Compose)
- DNS configuration for client resolution

## Timeline

This deployment model is under development. Contributions and feedback are welcome. Track progress in the project's issue tracker.

## Related Documentation

- [On-Premise Deployment](deployment-onpremise.md) -- Current recommended deployment
- [Architecture](architecture.md) -- System architecture overview
