#!/usr/bin/python

from datetime import datetime
from socket import *
from Crypto.Cipher import AES
import time
import random

class rm2:
  def __init__(self):
    self.count = random.randrange(0xffff) 
    self.key = bytearray([0x09, 0x76, 0x28, 0x34, 0x3f, 0xe9, 0x9e, 0x23, 0x76, 0x5c, 0x15, 0x13, 0xac, 0xcf, 0x8b, 0x02])
    self.iv = bytearray([0x56, 0x2e, 0x17, 0x99, 0x6d, 0x09, 0x3d, 0x28, 0xdd, 0xb3, 0xba, 0x69, 0x5a, 0x2e, 0x6f, 0x58])
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
    local_ip_address = s.getsockname()[0]

    self.address = local_ip_address.split('.')
    self.id = bytearray([0, 0, 0, 0])

  def discover(self):
    self.cs = socket(AF_INET, SOCK_DGRAM)
    self.cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    self.cs.bind(('',0)) 
    self.port = self.cs.getsockname()[1]

    packet = bytearray(0x30)

    year = datetime.now().year

    packet[0x08] = 0xf9
    packet[0x09] = 0xff
    packet[0x0a] = 0xff
    packet[0x0b] = 0xff
    packet[0x0c] = year & 0xff
    packet[0x0d] = year >> 8
    packet[0x0e] = datetime.now().minute
    packet[0x0f] = datetime.now().hour
    subyear = str(year)[2:]
    packet[0x10] = int(subyear)
    packet[0x11] = datetime.now().isoweekday()
    packet[0x12] = datetime.now().day
    packet[0x13] = datetime.now().month
    packet[0x18] = int(self.address[0])
    packet[0x19] = int(self.address[1])
    packet[0x1a] = int(self.address[2])
    packet[0x1b] = int(self.address[3])
    packet[0x1c] = self.port & 0xff
    packet[0x1d] = self.port >> 8
    packet[0x26] = 6
    checksum = 0xbeaf

    for i in range(len(packet)):
        checksum += packet[i]
    checksum = checksum & 0xffff
    packet[0x20] = checksum & 0xff
    packet[0x21] = checksum >> 8

    self.cs.sendto(packet, ('255.255.255.255', 80))
    response = self.cs.recvfrom(1024)
    responsepacket = bytearray(response[0])
    self.host = response[1]
    self.mac = responsepacket[0x3a:0x40]

  def auth(self):
    payload = bytearray(0x50)
    payload[0x04] = 0x31
    payload[0x05] = 0x31
    payload[0x06] = 0x31
    payload[0x07] = 0x31
    payload[0x08] = 0x31
    payload[0x09] = 0x31
    payload[0x0a] = 0x31
    payload[0x0b] = 0x31
    payload[0x0c] = 0x31
    payload[0x0d] = 0x31
    payload[0x0e] = 0x31
    payload[0x0f] = 0x31
    payload[0x10] = 0x31
    payload[0x11] = 0x31
    payload[0x12] = 0x31
    payload[0x1e] = 0x01
    payload[0x2d] = 0x01
    payload[0x30] = 'T'
    payload[0x31] = 'e'
    payload[0x32] = 's'
    payload[0x33] = 't'
    payload[0x34] = ' '
    payload[0x35] = ' '
    payload[0x36] = '1'

    response = self.send_packet(0x65, payload)

    enc_payload = response[0x38:]

    aes = AES.new(str(self.key), AES.MODE_CBC, str(self.iv))
    payload = aes.decrypt(str(response[0x38:]))

    self.id = payload[0x00:0x04]
    self.key = payload[0x04:0x14]

  def send_packet(self, command, payload):
    packet = bytearray(0x38)
    packet[0x00] = 0x5a
    packet[0x01] = 0xa5
    packet[0x02] = 0xaa
    packet[0x03] = 0x55
    packet[0x04] = 0x5a
    packet[0x05] = 0xa5
    packet[0x06] = 0xaa
    packet[0x07] = 0x55
    packet[0x24] = 0x2a
    packet[0x25] = 0x27
    packet[0x26] = command 
    packet[0x28] = self.count & 0xff 
    packet[0x29] = self.count >> 8 
    packet[0x2a] = self.mac[0]
    packet[0x2b] = self.mac[1]
    packet[0x2c] = self.mac[2]
    packet[0x2d] = self.mac[3]
    packet[0x2e] = self.mac[4]
    packet[0x2f] = self.mac[5]
    packet[0x30] = self.id[0]
    packet[0x31] = self.id[1]
    packet[0x32] = self.id[2]
    packet[0x33] = self.id[3]

    checksum = 0xbeaf
    for i in range(len(payload)):
      checksum += payload[i]
      checksum = checksum & 0xffff

    aes = AES.new(str(self.key), AES.MODE_CBC, str(self.iv))
    payload = aes.encrypt(str(payload))

    packet[0x34] = checksum & 0xff
    packet[0x35] = checksum >> 8

    for i in range(len(payload)):
      packet.append(payload[i])
    
    checksum = 0xbeaf
    for i in range(len(packet)):
      checksum += packet[i]
      checksum = checksum & 0xffff
    packet[0x20] = checksum & 0xff
    packet[0x21] = checksum >> 8

    self.cs.sendto(packet, self.host)
    response = self.cs.recvfrom(1024)
    return response[0]

  def send_data(self, data):
    packet = bytearray([0x02, 0x00, 0x00, 0x00])
    packet += data
    self.send_packet(0x6a, packet) 

  def enter_learning(self):
    packet = bytearray(16)
    packet[0] = 3
    self.send_packet(0x6a, packet) 
    
  def check_data(self):
    packet = bytearray(16)
    packet[0] = 4
    response = self.send_packet(0x6a, packet) 
    err = ord(response[0x22]) | (ord(response[0x23]) << 8)
    if err == 0:
      aes = AES.new(str(self.key), AES.MODE_CBC, str(self.iv))
      payload = aes.decrypt(str(response[0x38:]))
      return payload[0x04:]
