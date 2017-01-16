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
import sys
import json
import urwid
import socket
import _thread
from switch             import Switch
from .render            import SlideDisplay

def run_slides(projector):
    projector.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove('/tmp/sli-socket')
    except OSError:
        pass
    projector.socket.bind('/tmp/sli-socket')
    projector.socket.listen(1)
    projector.connection, addr = projector.socket.accept()
    while True:
        data = projector.connection.recv(1024)
        if not data:
            break
        json_data = json.loads(data)
        print(json_data)
        projector.slide_index = json_data['slide']
        projector.update_slide()

def run_notes(projector):
    projector.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    projector.socket.connect('/tmp/sli-socket')
    while True:
        data = projector.socket.recv(1024)
        if not data:
            break
        json_data = json.loads(data)
        print(json_data)
        projector.slide_index = json_data['slide']
        projector.update_slide()

class SlideProjector(object):
    def __init__(self, slide_deck, presenter_mode):
        self.slides = slide_deck.slides
        self.slide_index = 0
        self.renderer = SlideDisplay()
        self.notes_mode = presenter_mode
        self.slide_display = None
        self.connection = None
        if not self.notes_mode:
            _thread.start_new_thread(run_slides, (self,))
        else:
            _thread.start_new_thread(run_notes, (self,))

    def send_data(self, data):
        raw_data = str.encode(data)
        if not self.notes_mode:
            self.connection.send(raw_data)
        else:
            try: self.socket.send(raw_data)
            except: pass

    def next_slide(self):
        should_advance = self.slide_index + 1 < len(self.slides)
        if should_advance:
            self.slide_index += 1
            json_data = json.dumps({'slide':self.slide_index})
            self.send_data(json_data)
        return should_advance

    def prev_slide(self):
        should_backtrack = self.slide_index > 0
        if should_backtrack:
            self.slide_index -= 1
            json_data = json.dumps({'slide':self.slide_index})
            self.send_data(json_data)
        return should_backtrack

    def update_slide(self):
        if self.slide_display is None:
            return
        self.slide_display.set_text("%d" % self.slide_index)

    def run(self):
        self.slide_display = urwid.Text('')
        def input_handler(keys, raw):
            first_key = keys[0]
            with Switch(first_key) as case:
                if case('Q') or case('q'): self.exit()
                if case('left'): self.prev_slide()
                if case('right'): self.next_slide()
            # self.renderer.feed(self.slides[self.slide_index])
            self.update_slide()
        fill = urwid.Filler(self.slide_display, 'top')
        loop = urwid.MainLoop(fill, input_filter=input_handler)
        loop.run()

    def exit(self):
        urwid.ExitMainLoop()
        if not self.notes_mode:
            self.connection.close()
        sys.exit(0)
