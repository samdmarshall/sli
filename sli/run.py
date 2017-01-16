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
import tty
import curses
import string
import termios
import blessings
from switch             import Switch
from .render            import SlideDisplay

BINDABLES = string.ascii_letters + string.digits + string.whitespace

class _Getch:
    def __call__(self):
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch not in BINDABLES:
                    ch += sys.stdin.read(2)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

class SlideProjector(object):
    def __init__(self, slide_deck):
        self.slides = slide_deck.slides
        self.input = _Getch()
        self.slide_index = 0
        self.term = blessings.Terminal()
        self.renderer = SlideDisplay()
        self.renderer.set_terminal(self.term)
        self.term.enter_fullscreen()
        self.term.stream.write(self.term.hide_cursor)

    def flash(self):
        print('\a')
        print(self.term.move(0,0))

    def next(self):
        new_slide = False
        if self.slide_index + 1 < len(self.slides):
            self.slide_index += 1
            new_slide = True
        else:
            self.flash()
        return new_slide

    def back(self):
        new_slide = False
        if self.slide_index > 0:
            self.slide_index -= 1
            new_slide = True
        else:
            self.flash()
        return new_slide

    def separator(self):
        separator_bar = '=' * (self.term.width - 2)
        separator_string = '@'+separator_bar+'@'
        return separator_string
        
    def run(self):
        new_slide = True
        should_run = True
        while should_run:
            if new_slide:
                new_slide = False
                print(self.term.clear())
                print(self.separator())
                print(self.term.clear())
                self.term.move(0,0)
                self.renderer.feed(self.slides[self.slide_index])
            key = self.input()
            with Switch(key) as case:
                if case('\x1b[D'):
                    new_slide = self.back()
                if case('\x1b[C'):
                    new_slide = self.next()
                if case('q'):
                    self.exit()

    def exit(self):
        self.term.stream.write(self.term.normal_cursor)
        self.term.exit_fullscreen()
        sys.exit(0)
