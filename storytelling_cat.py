#!/usr/bin/env python
import os
import signal
from itertools import cycle
from os import path
from Queue import Queue
from subprocess import Popen, PIPE, check_output
from threading import Thread
from time import sleep

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


def get_child_pid(pid):
    return int(check_output('ps -o pid --ppid {} --noheaders'.format(int(pid)), shell=True).strip())


class Executor(Thread):
    def __init__(self, sounds_dir):
        super(Executor, self).__init__()
        self.sounds_dir = sounds_dir

    def run(self):
        sound_list = [i for i in os.listdir(self.sounds_dir) if i.lower().endswith('.mp3')]
        if not sound_list:
            print('no sounds available!')
            return

        player_pid = None
        sounds = cycle(sound_list)

        while True:
            sleep(0.1)
            command = commands.get()
            print(command)

            if command == 'QUIT':
                if player_pid is not None:
                    try:
                        os.kill(player_pid, signal.SIGTERM)
                    except OSError:
                        pass
                return

            if command == 'PLAY_NEXT':
                sound_file = path.join(self.sounds_dir, next(sounds))

                if player_pid is not None:
                    try:
                        os.kill(player_pid, signal.SIGTERM)
                    except OSError:
                        pass

                shell = Popen('/usr/bin/mpg123 -C --ctrlusr1 s "{}"'.format(sound_file), shell=True)
                player_pid = get_child_pid(shell.pid)

            if command == 'PLAY_PAUSE':
                if player_pid is None:
                    commands.put('PLAY_NEXT')
                    continue

                try:
                    os.kill(player_pid, signal.SIGUSR1)
                except OSError:
                    pass


def run_keyboard(sounds_dir):
    executor = Executor(sounds_dir)
    executor.start()
    getcher = Getch()

    while True:
        key = getcher()

        if key == 'q':
            commands.put('QUIT')
            return

        if key == 'n':
            commands.put('PLAY_NEXT')

        if key == 'a':
            commands.put('PLAY_PAUSE')

        sleep(0.2)


def run_raspberrypi(sounds_dir):
    executor = Executor(sounds_dir)
    executor.start()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyboard', action='store_true')
    parser.add_argument('--sounds-dir', default='/usr/share/catsounds')

    args = parser.parse_args()

    if args.keyboard:
        run_keyboard(args.sounds_dir)
    else:
        run_raspberrypi(args.sounds_dir)


if __name__ == '__main__':
    main()
