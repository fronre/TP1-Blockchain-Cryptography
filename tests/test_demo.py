import json
import socket
import time

from blockchain_tp1.socket_demo import build_nodes


def test_four_node_demo_can_send_local_messages():
    nodes = build_nodes()
    sender = nodes["alice"]
    receiver = nodes["bob"]

    payload = {"type": "ping", "message": "hello bob"}
    frame = {"from": sender.name, "to": receiver.name, "payload": payload}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 5001))
        sock.sendall(json.dumps(frame).encode("utf-8"))
        ack = sock.recv(1024)
        assert ack == b"ACK"

    time.sleep(0.1)
    assert any(msg.get("to") == "bob" for msg in receiver.incoming_messages)


def test_encrypted_message_exchange_between_nodes():
    nodes = build_nodes()
    response = nodes["alice"].send_encrypted_message("bob", "s3cret message")
    assert response["from"] == "alice"
    assert response["to"] == "bob"
    time.sleep(0.1)
    received = [msg for msg in nodes["bob"].incoming_messages if msg.get("from") == "alice"]
    assert received and received[-1]["payload"]["message"] == "s3cret message"
