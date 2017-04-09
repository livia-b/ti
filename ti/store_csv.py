# coding: utf-8
from .store import Store
import os
import csv
import logging
from collections import defaultdict

class Store_csv(Store):
    default_store_filename = '.ti-sheet.csv'

    def __init__(self, store_path = None):
        if store_path is None:
            store_path = self.default_store_path()
        self.store_path = store_path
        if not os.path.isfile(store_path):
            self.dump([dict( zip(self.fields, self.fields )) ])
        else:
            fieldnames = self.load(drop_headers=False)[0]
            if not set(self.fields) == set(fieldnames.keys()):
                logging.error("Wrong format in file %s" %self.store_path)
                raise ValueError()

    def load(self, drop_headers = True, sort_by_startdate = True):


        with open(self.store_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=self.fields)
            rows = list(reader)[int(drop_headers):]
        if sort_by_startdate:
            ordered_rows = sorted([(row['start_date'], row) for row in rows])
            rows = [ row for (start_date, row)  in ordered_rows ]
        return rows

    def _append_entry(self, row):
        with open(self.store_path, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writerow(row)

    def dump(self, rows):
        with open(self.store_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writerows(rows)

    def get_current(self):
        """
        get last row if still running
        :return: 
        """
        rows = self.load()
        if len(rows) == 0:
            return None
        lastrow = rows[-1]
        if lastrow['is_current'] == 'True':
            return lastrow
        else:
            return None

    def add_tracking(self, task, project, start):
        row = dict(start=str(start),
                   start_date = str(start.to_date_string()),
                   is_current = 'True',
                   project = project,
                   task = task)
        self._append_entry(row)

    def finish_tracking(self, current, task_end):
        entries = self.load()
        last_entry = entries[-1]
        if not last_entry == current:
            raise ValueError("Inconsistent entries")

        last_entry.update({
            'is_current' : '', #its boolean value is False
            'end' : str(task_end),
            'in_seconds' : str((task_end - current['start']).total_seconds())
        })
        self.dump(entries)

    def get_logs(self, gte, lte):
        for row in self.load():
            if gte <= row['start_date']  <= lte:
                yield row

    def get_aggregated_logs(self, gte, lte):
        durations = defaultdict(lambda: 0)
        for entry in self.get_logs(gte, lte):
            durations[(entry['project'], entry['task'])] += float( entry['in_seconds'])
        for (p,t), s in durations.items():
            yield dict(
                project = p,
                task = t,
                total_seconds =s
            )

    def edit(self, cmd):
        import subprocess
        subprocess.check_call(cmd + ' ' + self.store_path, shell=True)














