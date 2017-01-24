#!/usr/bin/env python3
#
# Copyright (c) 2017, Samantha Marshall (http://pewpewthespells.com)
# All rights reserved.
#
# https://github.com/samdmarshall/sli
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# 3. Neither the name of Samantha Marshall nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import json
import socket

def start_client(agent):
    agent.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    agent.socket.connect(agent.address)
    read_stream(agent)

def start_server(agent):
    agent.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(agent.address)
    except OSError:
        pass
    agent.socket.bind(agent.address)
    agent.socket.listen(1)
    agent.connection, _ = agent.socket.accept()
    read_stream(agent)

def read_stream(agent):
    while True:
        data = agent.get_stream().recv(1024)
        if not data:
            break
        json_data = json.loads(data)
        agent.process(json_data)

def write_stream(agent, obj):
    json_data = json.dumps(obj)
    raw_data = str.encode(json_data)
    if agent.get_stream() is not None:
        try:
            agent.get_stream().send(raw_data)
        except:
            pass
    
