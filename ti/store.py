import abc
import os


class Store(object):
    fields = [
        'id', 'start', 'end', 'start_date', 'in_seconds', 'is_current', 'project', 'task']
    __metaclass__ = abc.ABCMeta
    default_store_folder = '~'
    default_store_filename = 'ti-sheet'

    @abc.abstractmethod
    def get_current(self):
        pass

    @abc.abstractmethod
    def add_tracking(self, task, project, start):
        pass

    @abc.abstractmethod
    def finish_tracking(self, current, task_end):
        pass

    @abc.abstractmethod
    def get_logs(self, gte, lte):
        pass

    @abc.abstractmethod
    def get_aggregated_logs(self, gte, lte):
        pass

    @abc.abstractmethod
    def edit(self, cmd):
        pass

    def default_store_path(self):
        store_path = os.path.expanduser(os.path.join(self.default_store_folder,
                                                     self.default_store_filename))
        return store_path