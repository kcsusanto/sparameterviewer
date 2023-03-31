#!/bin/python

import sys, os, logging

from gui.main_window import SparamviewerMainDialog
from gui.log_dialog import LogHandler
from lib import AppGlobal, is_windows


if __name__ == '__main__':

    
    # splashscreen (pyinstaller only)
    import importlib
    if importlib.find_loader('pyi_splash') is not None:
        import pyi_splash
        pyi_splash.update_text("Loading S-Parameter Viewer...")
        pyi_splash.close()
        

    AppGlobal.set_root_path(os.path.split(os.path.realpath(__file__))[0])

    LOG_FORMAT = '%(asctime)s: %(message)s (%(filename)s:%(lineno)d:%(funcName)s, %(levelname)s)'
    logging.captureWarnings(True)
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, stream=None)

    try:
        # add a second logger that logs critical errors to file
        logToFile = logging.FileHandler(os.path.join(AppGlobal.get_root_path(), 'sparamviewer.log'))
        logToFile.setFormatter(logging.Formatter(LOG_FORMAT))
        logToFile.setLevel(logging.ERROR)
        logging.getLogger().addHandler(logToFile)
    except Exception as ex:
        pass # ignore

    try:
        # disable log stuff I am not interested in
        logging.getLogger('matplotlib.font_manager').disabled = True
        logging.getLogger('matplotlib.ticker').disabled = True
    except Exception as ex:
        pass # ignore
    
    LogHandler.set_up()

    try:
        if is_windows():
            # hide terminal window
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception as ex:
        pass # ignore

    try:
        filenames = sys.argv[1:]
        app = SparamviewerMainDialog(filenames)
        app.run()
    except Exception as ex:
        logging.exception('Error in main loop: {ex}')
        sys.exit(1)
