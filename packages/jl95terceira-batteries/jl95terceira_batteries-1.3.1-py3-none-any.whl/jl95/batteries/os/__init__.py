from os import *

from .. import sys as _sys

TEMP_DIR = 'C:\\Temp' if _sys.is_this_windows() else \
           '/tmp'

def get_user_env(name  :str,
                 expand:bool=False):
    
    return (popen(f'powershell -NoProfile -Command "(Get-Item -Path HKCU:\\Environment).GetValue(\'{name}\')"')                                         if expand else \
            popen(f'powershell -NoProfile -Command "(Get-Item -Path HKCU:\\Environment).GetValue(\'{name}\', $null, \'DoNotExpandEnvironmentNames\')"')).read()
