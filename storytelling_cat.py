#!/usr/bin/env python
import signal
from Queue import Queue
from threading import Thread
from time import sleep
from os import path
from subprocess import Popen, PIPE

commands = Queue()


class Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


class Executor(Thread):
    def run(self):
        current_sound = 0
        player = None

        while True:
            sleep(0.1)
            command = commands.get()
            print command

            if command == 'QUIT':
                if player is not None:
                    player.terminate()
                return

            if command == 'PLAY_NEXT':
                next_sound = current_sound + 1
                sound_file = '/usr/share/catsounds/sound{}.mp3'.format(next_sound)
                
                if not path.isfile(sound_file):
                    if next_sound == 1:
                        print 'no sounds available!'
                        continue

                    current_sound = 0
                    commands.put('PLAY_NEXT')
                    continue

                if player is not None:
                    player.terminate()

                player = Popen(['/usr/bin/mpg123', '-C', '--ctrlusr1', 's', sound_file], stdin=PIPE)
                current_sound = next_sound

            if command == 'PLAY_PAUSE':
                if player is None:
                    commands.put('PLAY_NEXT')
                    continue

                player.send_signal(signal.SIGUSR1)


def run_keyboard():
    executor = Executor()
    executor.start()
    getcher = Getch()

    while True:
        key = getcher()

        if key == 'q':
            commands.put('QUIT')
            return

        if key == 'n':
            commands.put('PLAY_NEXT')

        if key == 'p':
            commands.put('PLAY_PAUSE')

        sleep(0.2)


def run_raspberrypi():
    executor = Executor()
    executor.start()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyboard', action='store_true')

    args = parser.parse_args()

    if args.keyboard:
        run_keyboard()
    else:
        run_raspberrypi()


if __name__ == '__main__':
    main()
