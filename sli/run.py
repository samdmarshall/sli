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
import socket
import _thread
import urwid
from switch             import Switch
from .render            import SlideDisplay

def read_stream(projector):
    while True:
        data = projector.get_stream().recv(1024)
        if not data:
            break
        json_data = json.loads(data)
        projector.update_slide(json_data['slide'])

def run_slides(projector):
    projector.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove('/tmp/sli-socket')
    except OSError:
        pass
    projector.socket.bind('/tmp/sli-socket')
    projector.socket.listen(1)
    projector.connection, _ = projector.socket.accept()
    read_stream(projector)

def run_notes(projector):
    projector.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    projector.socket.connect('/tmp/sli-socket')
    read_stream(projector)

class SlideProjector(object):
    def __init__(self, slide_deck, presenter_mode, slide_start_index):
        self.slides = slide_deck.slides
        slide_start_index = max(0, slide_start_index)
        last_slide_index = len(self.slides) - 1
        slide_start_index = min(last_slide_index, slide_start_index)
        self.slide_index = slide_start_index
        self.renderer = SlideDisplay()
        self.renderer.set_presenter_notes(presenter_mode)
        self.notes_mode = presenter_mode
        self.slide_display = None
        self.connection = None
        self.socket = None
        self.started_presentation = False
        if not self.notes_mode:
            _thread.start_new_thread(run_slides, (self,))
        else:
            _thread.start_new_thread(run_notes, (self,))

    def get_stream(self):
        if not self.notes_mode:
            return self.connection
        else:
            return self.socket

    def send_data(self):
        json_data = json.dumps({'slide':self.slide_index})
        raw_data = str.encode(json_data)
        if not self.notes_mode:
            if self.connection is not None:
                self.connection.send(raw_data)
        else:
            if self.socket is not None:
                try:
                    self.socket.send(raw_data)
                except:
                    pass

    def next_slide(self):
        if self.started_presentation is True:
            should_advance = self.slide_index + 1 < len(self.slides)
            if should_advance:
                self.slide_index += 1
                self.send_data()
            return should_advance
        return False

    def prev_slide(self):
        if self.started_presentation is True:
            should_backtrack = self.slide_index > 0
            if should_backtrack:
                self.slide_index -= 1
                self.send_data()
            return should_backtrack
        return False

    def update_slide(self, new_index=None):
        if new_index is None:
            new_index = self.slide_index
        if self.slide_display is None:
            return
        slide_contents = self.slides[new_index]
        self.renderer.reset_lines()
        self.renderer.feed(slide_contents)
        self.run_loop.draw_screen()

    def run(self):
        self.slide_display = urwid.Text('')
        self.renderer.set_display_driver(self.slide_display)
        def input_handler(keys, raw):
            first_key = keys[0]
            with Switch(first_key) as case:
                if case('ctrl q'):
                    self.exit()
                if case('left'):
                    self.prev_slide()
                if case('right'):
                    self.next_slide()
            if self.started_presentation is False:
                self.started_presentation = True
            self.update_slide()
        display_widget = urwid.Filler(self.slide_display, 'top')
        self.run_loop = urwid.MainLoop(display_widget, input_filter=input_handler)
        self.run_loop.run()

    def exit(self):
        if self.started_presentation is True:
            urwid.ExitMainLoop()
            if not self.notes_mode and self.connection is not None:
                self.connection.close()
            sys.exit(0)
