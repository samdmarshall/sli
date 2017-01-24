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

import sys
import urwid
from switch         import Switch
from .agent         import Client, Server
from .render        import SlideDisplay

class BaseDisplay(object):
    def __init__(self, delegate=None):
        self.widget = urwid.Widget()
        self.run_loop = None
        self.__delegate = delegate
    def update(self):
        if self.__delegate is not None:
            self.__delegate.update()
    def run(self):
        def input_handler(keys, raw):
            with Switch(keys[0]) as case:
                if case('space'):
                    self.__delegate.update()
                if case('ctrl q'):
                    self.exit()
                if keys[0] in self.__delegate.getInput().keys():
                    self.__delegate.getInput()[keys[0]]()
            self.update()
        self.run_loop = urwid.MainLoop(self.widget, input_filter=input_handler)
        self.run_loop.run()
    def exit(self):
        if self.__delegate is not None:
            self.__delegate.exit()
        urwid.ExitMainLoop()
        sys.exit(0)

class BaseDisplayDelegate(object):
    def __init__(self):
        self.__interior = BaseDisplay(self)
    def setWidget(self, widget):
        self.__interior.widget = widget
    def run(self):
        self.__interior.run()
    def update(self):
        pass
    def exit(self):
        pass
    def getInput(self):
        return {}
    def force_redraw(self):
        self.__interior.run_loop.draw_screen()

class SizingDisplay(BaseDisplayDelegate):
    def __init__(self):
        super().__init__()
        self.__text = urwid.Text('Hello World')
        self.setWidget(urwid.Filler(self.__text, 'top'))
    def update(self):
        self.__text.set_text('Goodbye World')

def calculate_starting_slide(input_number, slide_count):
    slide_start_index = max(0, input_number)
    last_slide_index = slide_count - 1
    slide_start_index = min(last_slide_index, slide_start_index)
    return slide_start_index

class SlideController(BaseDisplayDelegate):
    def __init__(self, slide_deck, slide_number, presenter_mode):
        super().__init__()
        self.slides = slide_deck.slides
        self.slide_index = calculate_starting_slide(slide_number, len(self.slides))
        self.started_presentation = False
        self.__text = urwid.Text('')
        self.setWidget(urwid.Filler(self.__text, 'top'))
        self.renderer = SlideDisplay()
        self.renderer.set_presenter_notes(presenter_mode)
        self.renderer.set_display_driver(self.__text)
        if not presenter_mode:
            self.agent = Server()
        else:
            self.agent = Client()
        self.agent.update_delegate = self
        self.agent.start()
    def getInput(self):
        accepted_input = {
            'left':  self.prev_slide,
            'right': self.next_slide,
        }
        return accepted_input
    def next_slide(self):
        should_advance = self.slide_index + 1 < len(self.slides)
        if should_advance:
            self.slide_index += 1
            self.agent.send_data({'slide':self.slide_index})
        return should_advance
    def prev_slide(self):
        should_backtrack = self.slide_index > 0
        if should_backtrack:
            self.slide_index -= 1
            self.agent.send_data({'slide':self.slide_index})
        return should_backtrack
    def process_update(self, data):
        if 'slide' in data.keys():
            self.slide_index = data['slide']
        self.update()
    def update(self):
        if self.__text is None:
            return
        slide_contents = self.slides[self.slide_index]
        self.renderer.reset_lines()
        self.renderer.feed(slide_contents)
        self.force_redraw()
class PresentationDisplay(SlideController):
    def __init__(self, slide_deck, slide_number, presenter_mode=False):
        super().__init__(slide_deck, slide_number, presenter_mode)
class SpeakerNotesDisplay(SlideController):
    def __init__(self, slide_deck, slide_number, presenter_mode=True):
        super().__init__(slide_deck, slide_number, presenter_mode)
