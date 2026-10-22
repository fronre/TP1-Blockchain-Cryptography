from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path

from .ca import CertificateAuthority
from .node import BlockchainNode

HOST = "127.0.0.1"
PORTS = {"alice": 5001, "bob": 5002, "carol": 5003, "dave": 5004}
_DEMO_STATE: dict[str, object] | None = None


def ensure_demo_material() -> None:
    authority = CertificateAuthority()
    authority.create_root_ca()
    for name in ["alice", "bob", "carol", "dave"]:
        authority.create_node_cert(name)


def _start_demo_servers(nodes: dict[str, BlockchainNode]) -> tuple[threading.Event, list[threading.Thread]]:
    global _DEMO_STATE
    stop_event = threading.Event()
    threads = []
    for node in nodes.values():
        t = threading.Thread(target=node.run_server, args=(stop_event,), daemon=True)
        threads.append(t)
        t.start()
    time.sleep(0.2)
    _DEMO_STATE = {"stop_event": stop_event, "threads": threads}
    return stop_event, threads


def build_nodes() -> dict[str, BlockchainNode]:
    ensure_demo_material()
    nodes = {}
    for name in ["alice", "bob", "carol", "dave"]:
        nodes[name] = BlockchainNode(name, Path("ca/ca.crt"), Path("nodes"), port=PORTS[name])
    if _DEMO_STATE is None:
        _start_demo_servers(nodes)
    return nodes


def start_all_nodes() -> dict[str, BlockchainNode]:
    return build_nodes()


def send_local_message(nodes: dict[str, BlockchainNode], sender_name: str, receiver_name: str, message: str) -> dict:
    sender = nodes[sender_name]
    receiver = nodes[receiver_name]
    sender.send_encrypted_message(receiver_name, message)
    time.sleep(0.1)
    latest = [msg for msg in receiver.incoming_messages if msg.get("from") == sender_name]
    return latest[-1] if latest else {"error": "message not received"}


def main() -> None:
    nodes = start_all_nodes()
    result = send_local_message(nodes, "alice", "bob", "hello from alice")
    print(json.dumps(result, indent=2))
    if _DEMO_STATE is not None:
        _DEMO_STATE["stop_event"].set()
        for thread in _DEMO_STATE["threads"]:
            thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
