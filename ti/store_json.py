from ti.store import Store
import  os
import json
import yaml
import tempfile
import subprocess
import logging

class Store_json(Store):
    default_store_filename = '.ti-sheet'

    def __init__(self, store_path):
        self.store_path = store_path

    def load(self):

        if os.path.exists(self.store_path):
            with open(self.store_path) as f:
                data = json.load(f)

        else:
            data = {'work': [], 'interrupt_stack': []}

        return data

    def dump(self, data):
        with open(self.store_path, 'w') as f:
            json.dump(data, f, separators=(',', ': '), indent=2)

    def edit(self, cmd):

        data = self.load()
        yml = yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)

        fd, temp_path = tempfile.mkstemp(prefix='ti.')
        with open(temp_path, "r+") as f:
            f.write(yml.replace('\n- ', '\n\n- '))
            f.seek(0)
            subprocess.check_call(cmd + ' ' + temp_path, shell=True)
            yml = f.read()
            f.truncate()
            f.close()

        os.close(fd)
        os.remove(temp_path)

        try:
            data = yaml.load(yml)
        except:
            logging.error("Oops, that YAML didn't appear to be valid!")
            raise SystemExit(1)

        self.dump(data)





