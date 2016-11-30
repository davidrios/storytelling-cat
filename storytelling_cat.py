#!/usr/bin/env python
import os
from itertools import cycle
from os import path
from Queue import Queue
from threading import Thread
from time import sleep, time

import pygame

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
    def __init__(self, sounds_dir):
        super(Executor, self).__init__()
        self.sounds_dir = sounds_dir

    def run(self):
        sound_list = [i for i in os.listdir(self.sounds_dir) if i.lower().endswith('.mp3')]
        if not sound_list:
            print('no sounds available!')
            return

        pygame.init()
        pygame.mixer.init()
        sounds = cycle(sound_list)
        playing = False

        while True:
            sleep(0.1)
            command = commands.get()
            print(command)

            if command == 'QUIT':
                pygame.mixer.quit()
                pygame.quit()
                return

            if command == 'PLAY_NEXT':
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path.join(self.sounds_dir, next(sounds)))
                pygame.mixer.music.play()
                playing = True

            if command == 'PLAY_PAUSE':
                if not pygame.mixer.music.get_busy():
                    commands.put('PLAY_NEXT')
                    continue

                if playing:
                    pygame.mixer.music.pause()
                    playing = False
                else:
                    pygame.mixer.music.unpause()
                    playing = True


def run_keyboard(sounds_dir):
    executor = Executor(sounds_dir)
    executor.daemon = True
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


def run_raspberrypi(sounds_dir):
    from RPi import GPIO

    executor = Executor(sounds_dir)
    executor.daemon = True
    executor.start()

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    last_state = True
    last_press = time()

    while True:
        input_state = GPIO.input(18)
        if input_state != last_state:
            if last_state:
                last_press = time()
            else:
                if time() - last_press >= 3:
                    commands.put('PLAY_NEXT')
                else:
                    commands.put('PLAY_PAUSE')

            last_state = input_state

        sleep(0.1)


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
