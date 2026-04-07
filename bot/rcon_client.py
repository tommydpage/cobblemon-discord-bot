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


class RconClient:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.request_id_counter = 0
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        auth_packet = build_packet(self.request_id_counter, 3, self.password)
        self.writer.write(auth_packet)
        await self.writer.drain()

        response_id, response_payload = parse_response(await self.reader.read(4096))
        if self.request_id_counter == response_id:
            print("Connection succesful! Server says: " + response_payload)
            status = True
        else:
            print("Connection unsuccesful. Server says: " + response_payload)
            status = False
            
        self.request_id_counter += 1
        return status
    

    async def send_command(self, payload):
        command = build_packet(self.request_id_counter, 2, payload)
        self.writer.write(command)
        await self.writer.drain()

        _, response_payload = parse_response(await self.reader.read(4096))
        self.request_id_counter += 1
        return response_payload
    
    async def disconnect(self):
        self.writer.close()
        await self.writer.wait_closed()

        self.reader = None
        self.writer = None
