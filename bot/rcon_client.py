"""
RCON client for Minecraft server communication.

Implements the Source RCON protocol over TCP to send commands
to the Minecraft server and receive responses.

Protocol spec: https://developer.valvesoftware.com/wiki/Source_RCON_Protocol
"""

import asyncio
import struct
import logging

logger = logging.getLogger(__name__)

def build_packet(request_id, packet_type, payload_string):
    packet = struct.pack('<i', request_id) + struct.pack('<i', packet_type) + payload_string.encode('utf-8') + b'\x00\x00'
    return struct.pack('<i', len(packet)) + packet

def parse_response(response):
    request_id = struct.unpack('<i', response[4:8])[0]
    payload_string = response[12:-2].decode('utf-8')
    return request_id, payload_string