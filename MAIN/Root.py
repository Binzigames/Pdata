#import libs
import sys

from MAIN.ADDITIONS.LIBS import *
from MAIN.ADDITIONS.Static import *

#boot-functions
def visuals():
    pass

def logic():
    pass


#boot
def root():
    logic()
    if is_editor_boot:
     visuals()

def boot_root():
    if not pr.window_should_close():
        root()
    else:
        pr.close_window()
        sys.exit(0)