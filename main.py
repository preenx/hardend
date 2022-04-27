# pylint: disable=unused-import, reimported, multiple-statements, wrong-import-position, ungrouped-imports
from ctypes import util
import os; os.sys.dont_write_bytecode = True
import utils
from libs import pynquirer, synscan
from interfaces import camera, mount
from models import camera, mount
from interfaces import telescope
from models import telescope

def main():
    utils.installation_warning()
    additional_project_urls = utils.get_project_url()
    selected_path = pynquirer.select('select server path', [
        *additional_project_urls, 'http://localhost:5000', 'http://10.11.11.9:5000'
    ])
    subpath = ('/' if selected_path[-5:] == ':5000' else '/telescope_module/')
    workmode = pynquirer.select('select work mode', ['mock', 'real'])
    telescope_instance = telescope.telescope_factory(
        workmode=workmode, server={'path': selected_path, 'subpath': subpath}
    )
    telescope_instance.serve()
    utils.kill_all_threads()

if __name__ == '__main__':
    main()
