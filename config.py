from utils import sysModel
import os

# Command code
PROGRAM_CLOSE = 'quit'
COMMAND_CHECKED = 'command'
NO_COMMAND_CHECKED = 'not command'

# time difference
BROKER_TIME_BETWEEN_UTC = 2 # utc_diff: difference between broker (UTC+3) and UTC = 3 (see note 23a) and (note 56b)
DOWNLOADED_MIN_DATA_TIME_BETWEEN_UTC = 5 # that is without daylight shift time (UTC+5)

PRJPATH = sysModel.getTargetPath('210215_mt5_2')
DOCSPATH = os.path.join(PRJPATH, 'docs')

# records
RECORDS_PATH = os.path.join(DOCSPATH, "records")

# for parameters
PARAMS_PATH = os.path.join(DOCSPATH, "params")
PARAMS_FILENAME = 'params.txt'
PARAMS_TEXT = ''