# coding: utf-8
"""
ti is a simple and extensible time tracker for the command line. Visit the
project page (http://ti.sharats.me) for more details.
"""
import argparse
from .actions import  Actions
import sys
import os

usage = """ ti <command> [<args>]

ti is a simple and extensible time tracker for the command line.
Visit the project page (http://ti.sharats.me) for more details.

Commands:
  --no-color
  o, on        Start new tracking
  f, fin       Stop currently running tracking
  s, status    Show current status
  l, log       List time logs for period with possible values today (default), week or month
  r, report    Aggregated report for period with possible values today (default), week or month
  e, edit

Old commands:
  ti (t|tag) <tag>...
  ti (n|note) <note-text>...

  ti (i|interrupt)

"""

# Inpired by Multi-level argparse by @chase_seibert
# http://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
class Ti(object):
    valid_commands = {
        'on': ['o', 'on'],
        'fin': ['f', 'fin'],
        'status': ['s', 'status'],
        'log': ['l', 'log'],
        'report': ['r', 'report'],
        'edit': ['e', 'edit']
    }
    actions = None

    def __init__(self, store_file ):
        self.actions = Actions( store_file)
        parser = argparse.ArgumentParser(
            usage=usage)
        parser.add_argument('command', help='Subcommand to run')
        parser.add_argument('--no-color', default=False, action="store_true",
                            help="don't use color in console output")

        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])

        reverse_map = {}
        for k, v1 in self.valid_commands.items():
            for v2 in v1:
                reverse_map[v2] = k

        if args.command not in reverse_map:
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, reverse_map[args.command])()

    def on(self):
        parser = argparse.ArgumentParser(
            prog='ti on',
            description='Track new task')

        parser.add_argument('task', type=str, nargs="?", help="name of task")
        parser.add_argument('project', type=str, nargs="?", help="group task and tracking under project, "
                                                                 "useful for aggregation")
        parser.add_argument('--ago', type=str, metavar="time",
                            help="shift start of tracking into past, eg. 10 minutes")

        args = parser.parse_args(sys.argv[2:])
        self.actions.action_on(**vars(args))

    def fin(self):
        parser = argparse.ArgumentParser(
            prog='ti fin',
            description='Finish running task')
        parser.add_argument('--ago', type=str, metavar="time",
                            help="shift finish of tracking into past, e.g. 10 minutes")

        args = parser.parse_args(sys.argv[2:])
        self.actions.action_fin(**vars(args))

    def status(self):
        parser = argparse.ArgumentParser(
            prog='ti status',
            description='Get current status')
        parser.add_argument('--short', default=False, action="store_true",
                            help="short status ideal for integration to other tools e.g. bash prompt")

        args = parser.parse_args(sys.argv[2:])
        self.actions.action_status(**vars(args))

    def log(self):
        parser = argparse.ArgumentParser(
            prog='ti log',
            description='List of time logs for selected period')
        parser.add_argument('period', type=str, metavar="time", nargs="?", default='today',
                            choices=['today', 'week', 'month'],
                            help="period of time, possible choices: today (default), week or month")

        args = parser.parse_args(sys.argv[2:])
        self.actions.action_log(**vars(args))

    def report(self):
        parser = argparse.ArgumentParser(
            prog='ti report',
            description='Aggregated report of time logs for selected period')
        parser.add_argument('period', type=str, metavar="time", nargs="?", default='today',
                            choices=['today', 'week', 'month'],
                            help="period of time, possible choices: today (default), week or month")

        args = parser.parse_args(sys.argv[2:])
        self.actions.action_report(**vars(args))

    def edit(self):
        parser = argparse.ArgumentParser(
            prog='ti edit',
            description='edit')
        args = parser.parse_args(sys.argv[2:])
        self.actions.action_edit(**vars(args))


def main():
    Ti(os.environ.get('TI-SHEET',None))

if __name__ == '__main__':
    main()
