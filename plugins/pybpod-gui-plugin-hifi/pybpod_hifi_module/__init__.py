__version__ = '0.1.0'
__license__ = "MIT"
__status__ = "Development"

from confapp import conf

conf += 'pybpod_hifi_module.settings'

from pybpod_hifi_module.module import HiFi as BpodModule
