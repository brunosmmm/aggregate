import os
import glob

MODULE_LIST = glob.glob(os.path.dirname(__file__)+'/*.py')
MODULES = [os.path.basename(f)[:-3] for f in MODULE_LIST if os.path.isfile(f)]
