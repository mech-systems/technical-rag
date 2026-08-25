# WireGuard

WireGuard is a VPN protocol used to create encrypted network tunnels between peers.

Each peer has a private key and a corresponding public key. The private key must remain secret. The public key is shared with other peers.

## Configuration

A WireGuard configuration commonly contains:

- `PrivateKey`: private key of the local peer
- `PublicKey`: public key of the remote peer
- `Endpoint`: address and UDP port of the remote peer
- `AllowedIPs`: IP addresses routed through or accepted from the peer
- `PersistentKeepalive`: optional keepalive interval for peers behind NAT

## Interface management

Start an interface:

```bash
sudo wg-quick up wg0
