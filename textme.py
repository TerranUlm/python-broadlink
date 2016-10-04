#!/usr/bin/python

import broadlink

device = broadlink.rm2()
device.discover()
device.auth()