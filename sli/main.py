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
import argparse
from switch             import Switch
from .version           import __version__ as SLI_VERSION
from .reel              import SlideReel
from .                  import term
from .ui                import SizingDisplay, PresentationDisplay, SpeakerNotesDisplay
from .Logger            import Logger

def main():
    parser = argparse.ArgumentParser(description='command line markdown presenter')
    parser.add_argument(
        '--version',
        help='Displays the version information',
        action='version',
        version=SLI_VERSION,
    )
    parser.add_argument(
        '--quiet',
        help='Silences all logging output',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--verbose',
        help='Adds verbosity to logging output',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--no-ansi',
        help='Disables the ANSI color codes as part of the logger',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--debug',
        help=argparse.SUPPRESS,
        default=False,
        action='store_true'
    )

    if term.uses_suitable_locale() is False:
        Logger.write().error('Unable to initialize in this terminal, please uses a UTF-8 locale!')
        parser.exit(1, '')

    subparsers = parser.add_subparsers(title='Subcommands', dest='command')
    subparsers.required = True

    # Subcommand for running in presentation mode
    ##
    presentation_parser = subparsers.add_parser(
        'present',
        help='run sli in presentation mode',
    )
    presentation_parser.add_argument(
        'presentation',
        metavar='<path to presentation>',
        action='store',
    )
    presentation_parser.add_argument(
        '--slide',
        help='Specify the slide number to start on',
        action='store',
        type=int,
        default=0
    )

    # Subcommand for running in "speaker notes" mode
    ##
    speaker_notes_parser = subparsers.add_parser(
        'notes',
        help='run sli in speaker notes mode',
    )
    speaker_notes_parser.add_argument(
        'presentation',
        metavar='<path to presentation>',
        action='store',
    )
    speaker_notes_parser.add_argument(
        '--slide',
        help='Specify the slide number to start on',
        action='store',
        type=int,
        default=0
    )

    # Subcommand for running in "sizing" mode
    ##
    sizing_parser = subparsers.add_parser(
        'size',
        help='run sli in a debug mode to help size it correctly for display',
    )

    args = parser.parse_args()

    Logger.disableANSI(args.no_ansi)
    Logger.enableDebugLogger(args.debug)
    Logger.isVerbose(args.verbose)
    Logger.isSilent(args.quiet)

    with Switch(args.command) as case:
        if case('present'):
            slide_deck = SlideReel(args.presentation)
            presentation = PresentationDisplay(slide_deck, args.slide)
            presentation.run()
        if case('notes'):
            slide_deck = SlideReel(args.presentation)
            presentation = SpeakerNotesDisplay(slide_deck, args.slide)
            presentation.run()
        if case('size'):
            sizing_display = SizingDisplay()
            sizing_display.run()

if __name__ == '__main__':
    main()
