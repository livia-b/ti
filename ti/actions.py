# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import pendulum
import yaml
import os
import subprocess
import sys
import tempfile
from pytimeparse.timeparse import timeparse
from datetime import timedelta
from collections import defaultdict
from tabulate import tabulate
from .store import Store
from .git import Git
from .colors import red, yellow, green
from .utils import seconds_to_hours_and_minutes


class Actions(object):
    store = None
    equal_to_last = {}
    subtotals_count = 0
    subtotals_sum = 0
    subtotals_key = None

    def __init__(self, store_file_path=None):
        if store_file_path is None:
            ext = ''
        else:
            _, ext = os.path.splitext(store_file_path)

        store = {
            '.csv' : 'csv',
            '.sqlite': 'sqlite',
            '.json' : 'json',
            '.txt' : 'csv'
        }
        store_type = store.get(ext, 'csv')
        if store_type == 'csv':
            from .store_csv import Store_csv
            self.store = Store_csv(store_file_path)
        elif store_type == 'json':
            from .store_json import Store_json
            self.store = Store_json(store_file_path)
        self.use_color = True

    def red(self, txt):
        return red(txt, self.use_color )

    def yellow(self, txt):
        return yellow(txt, self.use_color)

    def green(self,txt):
        return green(txt, self.use_color)

    def action_on(self, task=None, project=None, ago=None):
        git = Git()
        git_support = git.is_git_installed() & git.is_cwd_repo()
        # print('Is git installed: {}'.format(git.is_git_installed()))
        # print('Is cwd git repo: {}'.format(git.is_cwd_repo()))
        # print('Get top level: {}'.format(git.get_top_level()))
        # print('Get current branch: {}'.format(git.get_active_branch()))

        # project not set
        if project is None:
            if git_support:
                project_path = git.get_top_level()[1:]
                project = str(project_path).replace('/', '-')

        if task is None:
            if git_support:
                task = git.get_active_branch()
            else:
                task = os.path.basename(os.getcwd())

        now = pendulum.now()
        time_text = 'right now'
        verb_text = 'Starting'
        if ago:
            seconds_ago = timeparse(ago)
            now = now.subtract(seconds=seconds_ago)
            time_text = now.diff_for_humans()
            verb_text = 'Started'

        current = self.store.get_current()
        if current:
            print('You are already working on task {}. Stop it or use a different sheet.'.format(self.green(current['task'])),
                  file=sys.stderr)
            raise SystemExit(1)

        self.store.add_tracking(task, project, now)

        print('{} working on task {}{} {}.'.format(
            verb_text,
            self.green(task),
            ' of project {}'.format(self.red(project)) if project else '',
            self.yellow(time_text)
        ))

    # def action_fin(time, back_from_interrupt=True):
    def action_fin(self, ago):
        current = self.ensure_working()

        now = pendulum.now()
        if ago:
            seconds_ago = timeparse(ago)
            now = now.subtract(seconds=seconds_ago)

        self.store.finish_tracking(current, now)
        print('You were working on {}{} for {} and task is stopped now.'.format(
            self.green(current['task']),
            ' of project {}'.format(
                self.red(current['project'])) if current['project'] else '',
            now.diff_for_humans(current['start'], absolute=True)
        ))

        # if back_from_interrupt and len(data['interrupt_stack']) > 0:
        #     name = data['interrupt_stack'].pop()['name']
        #     store.dump(data)
        #     action_on(name, time)
        #     if len(data['interrupt_stack']) > 0:
        #         print('You are now %d deep in interrupts.'
        #               % len(data['interrupt_stack']))
        #     else:
        #         print('Congrats, you\'re out of interrupts!')

    def action_status(self, short):
        try:
            current = self.ensure_working(silent=short)

            diff = pendulum.now().diff_for_humans(current['start'], absolute=True)
            if short:
                print('on {}/{} for {}.'.format(
                    self.red(current['project']),
                    self.green(current['task']),
                    diff))
            else:
                print('You have been working on {0} for {1}.'.format(
                    self.green(current['task']), diff))

        except SystemExit:
            if short:
                print('idle')

    def action_log(self, period):
        now = pendulum.now()

        data = []
        headers = []
        if period == 'today':
            today = now.to_date_string()
            results = self.store.get_logs(today, today)

            for log in results:
                start = pendulum.parse(log['start'])
                end = pendulum.parse(log['end'])

                data.append(
                    (
                        log['task'],
                        log['project'],
                        start.format('%H:%M'),
                        end.format('%H:%M'),
                        end.diff_for_humans(start, absolute=True),
                        '← yes' if log['is_current'] else ''
                    )
                )
                headers = [
                    'task',
                    'project',
                    'start',
                    'end',
                    'duration',
                    'current',
                ]
        elif period == 'week':
            results = self.store.get_logs(now.start_of('week').to_date_string(),
                                          now.end_of('week').to_date_string())

            for log in results:
                start = pendulum.parse(log['start'])
                end = pendulum.parse(log['end'])

                data.append(
                    (
                        log['task'],
                        log['project'],
                        self.none_if_equal_to_last('day_of_week', start.format('%A')),
                        self.none_if_equal_to_last('start_date', start.format('%d%_t %b')),
                        start.format('%H:%M'),
                        self.none_if_equal_to_last('end_date', end.format('%d%_t %b')),
                        end.format('%H:%M'),
                        end.diff_for_humans(start, absolute=True),

                        '← yes' if log['is_current'] else ''
                    )
                )
                headers = [
                    'task',
                    'project',
                    'day of week',
                    'start',
                    '',
                    'end',
                    '',
                    'duration',
                    'current',
                ]
        # period is month
        else:
            results = self.store.get_logs(now.start_of('month').to_date_string(),
                                          now.end_of('month').to_date_string())

            for log in results:
                start = pendulum.parse(log['start'])
                end = pendulum.parse(log['end'])

                data.append(
                    (
                        log['task'],
                        log['project'],
                        self.none_if_equal_to_last('day_of_week', start.format('%A')),
                        self.none_if_equal_to_last('start_date', start.format('%d%_t %b')),
                        start.format('%H:%M'),
                        self.none_if_equal_to_last('end_date', end.format('%d%_t %b')),
                        end.format('%H:%M'),
                        end.diff_for_humans(start, absolute=True),

                        '← yes' if log['is_current'] else ''
                    )
                )
                headers = [
                    'task',
                    'project',
                    'day of week',
                    'start',
                    '',
                    'end',
                    '',
                    'duration',
                    'current',
                ]
        print('\n' + tabulate(data, headers=headers))

    def action_report(self, period = 'month', period_end = None, split_day = True):
        now = pendulum.now()

        if period == 'today':
            today = now.to_date_string()
            period = today
            period_end = today

        elif period == 'week':
            period = now.start_of('week').to_date_string()
            period_end = now.end_of('week').to_date_string()

        elif period == 'month':
            period = now.start_of('month').to_date_string()
            period_end = now.end_of('month').to_date_string()

        else:
            if period_end is None:
                period_end = now.to_date_string()

        if split_day:
            sub_period_start = pendulum.parse(period)
            sub_period_end = sub_period_start.add(days=1)
            while (sub_period_end <= period_end):
                print(sub_period_start.to_formatted_date_string())
                self.action_report(sub_period_start.to_date_string(), sub_period_end.to_date_string(), split_day=False)
                sub_period_start = sub_period_end
                sub_period_end = sub_period_end.add(days=1)

        results = self.store.get_aggregated_logs(period, period_end)

        data = []
        headers = [
            'project',
            'task',
            'task total',
            'project total',
            'total'
        ]
        total = 0
        for log in results:
            if log.get('total_seconds', None) is None:
                print ("Task {} is still running, excluded from report".format(log['task']))
                continue
            total += log['total_seconds']
            subtotals = self.subtotals(log['project'], log['total_seconds'])
            if subtotals:
                data.append(
                    (
                        '-',
                        '-',
                        '-',
                        seconds_to_hours_and_minutes(subtotals),
                        ''
                    )
                )
            data.append(
                (
                    self.none_if_equal_to_last('project', log['project']),
                    log['task'],
                    seconds_to_hours_and_minutes(log['total_seconds']),
                    '',
                    ''
                )
            )
        # project subtotals
        subtotals = self.subtotals('', 0)
        if subtotals:
            data.append(
                (
                    '-',
                    '-',
                    '-',
                    seconds_to_hours_and_minutes(subtotals),
                    ''
                )
            )
        # totals
        data.append(
            (
                '',
                '',
                '',
                '',
                seconds_to_hours_and_minutes(total)
            )
        )
        print('\n' + tabulate(data, headers=headers, tablefmt='simple'))

    # def action_interrupt(name, time):
    #     ensure_working()
    #
    #     action_fin(time, back_from_interrupt=False)
    #
    #     data = store.load()
    #     if 'interrupt_stack' not in data:
    #         data['interrupt_stack'] = []
    #     interrupt_stack = data['interrupt_stack']
    #
    #     interrupted = data['work'][-1]
    #     interrupt_stack.append(interrupted)
    #     store.dump(data)
    #
    #     action_on('interrupt: ' + green(name), time)
    #     print('You are now %d deep in interrupts.' % len(interrupt_stack))
    #
    #
    # def action_note(content):
    #     ensure_working()
    #
    #     data = store.load()
    #     current = data['work'][-1]
    #
    #     if 'notes' not in current:
    #         current['notes'] = [content]
    #     else:
    #         current['notes'].append(content)
    #
    #     store.dump(data)
    #
    #     print('Yep, noted to ' + yellow(current['name']) + '.')
    #
    #
    # def action_tag(tags):
    #     ensure_working()
    #
    #     data = store.load()
    #     current = data['work'][-1]
    #
    #     current['tags'] = set(current.get('tags') or [])
    #     current['tags'].update(tags)
    #     current['tags'] = list(current['tags'])
    #
    #     store.dump(data)
    #
    #     tag_count = str(len(tags))
    #     print('Okay, tagged current work with ' + tag_count + ' tag' +
    #           ('s' if tag_count > 1 else '') + '.')
    #
    #
    def action_edit(self):
        if 'EDITOR' not in os.environ:
            print("Please set the 'EDITOR' environment variable", file=sys.stderr)
            raise SystemExit(1)

        self.store.edit(os.getenv('EDITOR'))



    def none_if_equal_to_last(self, key, value):
        if key in self.equal_to_last and self.equal_to_last[key] == value:
            return '-'

        else:
            self.equal_to_last[key] = value
            return value

    def subtotals(self, key, seconds):
        sum = False
        if key != self.subtotals_key:
            if self.subtotals_count > 1:
                sum = self.subtotals_sum
            self.subtotals_sum = seconds
            self.subtotals_key = key
            self.subtotals_count = 1
            return sum

        self.subtotals_sum += seconds
        self.subtotals_count += 1
        return sum

    def ensure_working(self, silent=False):
        current = self.store.get_current()
        if current:
            return current

        if not silent:
            print("For all I know, you aren't working on anything. "
                  "I don't know what to do.", file=sys.stderr)
            print('See `ti -h` to know how to start working.', file=sys.stderr)

        raise SystemExit(1)
