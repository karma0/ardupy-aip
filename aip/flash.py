

from pip._internal.cli.base_command import Command
from pip._internal.cli.req_command import RequirementCommand
from pip._internal.cli.status_codes import SUCCESS,ERROR
from pip._internal.utils import appdirs
from pip._internal.cli import cmdoptions
from pip._internal.network.download import Downloader
from pip._internal.models.link import Link

from pip._internal.operations.prepare import (
    _copy_source_tree,
    _download_http_url,
    unpack_url,
)
import os
import sys
from pathlib import Path
import platform
from  .serialUtils import SerialUtils
from .variable import *
import time


class flashCommand(RequirementCommand):
    """
    Show information about one or more installed packages.

    The output is in RFC-compliant mail header format.
    """
    name = 'flash'
    usage = """
      %prog [options] <package> ..."""
    summary = "flash all of package"
    ignore_require_venv = True

    def __init__(self, *args, **kw):
        super(flashCommand, self).__init__(*args, **kw)
        self.cmd_opts.add_option(
            '-a', '--ailes',
            dest='files',
            action='store_true',
            default=False,
            help='Show the full list of installed files for each package.')

        self.parser.insert_option_group(0, self.cmd_opts)
        self.user_data_dir = appdirs.user_data_dir(appname = "aip")

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.serial = SerialUtils()
        deploydir = Path(self.user_data_dir ,"deploy")
        self.ardupybin = str(Path(deploydir, "Ardupy.bin"))


    @property
    def stty(self):
        port,desc, hwid, isbootloader = self.serial.getAvailableBoard()
        if port == "None":
            print(port)
            return "echo not support"
        self.port = port
        if os.name == "posix":
            if platform.uname().system == "Darwin":
                return "stty -f " + port + " %d"
            return "stty -F " + port + " %d"
        elif os.name == "nt":
            return "MODE " + port + ":BAUD=%d PARITY=N DATA=8"
        return "echo not support"


    def run(self, options, args):
        bossacdir = Path(self.user_data_dir+"/ardupycore/Seeeduino/tools/bossac")
        print(str(bossacdir))
        if not os.path.exists(bossacdir) :
            os.makedirs(bossacdir)
        session = self.get_default_session(options)

        if sys.platform == "linux":
            link = Link("http://files.seeedstudio.com/arduino/tools/i686-linux-gnu/bossac-1.9.1-seeeduino-linux.tar.gz")
        if sys.platform == "win32":
            link = Link("http://files.seeedstudio.com/arduino/tools/i686-mingw32/bossac-1.9.1-seeeduino-windows.tar.bz2")
        if sys.platform == "darwin":
            link = Link("http://files.seeedstudio.com/arduino/tools/i386-apple-darwin11/bossac-1.9.1-seeeduino-drawin.tar.gz")

        bossac = Path(bossacdir,"bossac")
        if not os.path.exists(bossacdir):
            downloader = Downloader(session, progress_bar="on")
            unpack_url(
                link,
                bossacdir,
                downloader=downloader,
                download_dir=None,
            )
        try_count = 0
        do_bossac = True
        while True:
            if self.stty != "echo not support" :
                os.system(self.stty % 1200)
            #os.system(str(bossac)+ " --help")
            port,desc, hwid, isbootloader = self.serial.getAvailableBoard()
            time.sleep(1)
            if isbootloader == True:
                break
            try_count = try_count + 1
            if try_count == 5:
                do_bossac =  False
                break

        if do_bossac == True:
            print((str(bossac) + grove_ui_flashParam) % (self.port,  self.ardupybin))
            os.system((str(bossac) + grove_ui_flashParam) % (self.port,  self.ardupybin))
        else:
            print("Sorry, the device you should have is not plugged in")

        return SUCCESS




