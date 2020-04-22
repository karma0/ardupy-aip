
# The MIT License (MIT)
#
# Author: Baozhu Zuo (zuobaozhu@gmail.com)
#
# Copyright (C) 2020  Seeed Technology Co.,Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from pip._internal.cli.base_command import Command
from pip._internal.cli.req_command import RequirementCommand
from pip._internal.cli.status_codes import SUCCESS, ERROR
from pip._internal.cli import cmdoptions
from pip._internal.network.download import Downloader
from pip._internal.models.link import Link
from urllib.parse import urlparse

from pip._internal.operations.prepare import (
    _copy_source_tree,
    _download_http_url,
    unpack_url,
)

import os
import stat
from aip.variable import *
from aip.command import *
import shutil
from pathlib import Path

class installCommand(RequirementCommand):
    """
    Install Arudino Library binding with ArduPy.
    """
    name = 'install'
    usage = """
      %prog [options] <args> ..."""
    summary = "Install Arudino Library binding with ArduPy."
    ignore_require_venv = True

    def __init__(self, *args, **kw):
        super(installCommand, self).__init__(*args, **kw)

        self.cmd_opts.add_option(
            '-r', '--remove',
            dest='uninstall',
            action='store_true',
            default=False,
            help='Install the aip package')

        self.cmd_opts.add_option(
            '-l', '--list',
            dest='list',
            action='store_true',
            default=False,
            help='list all the aip package')

        self.cmd_opts.add_option(
            '-n', '--netloc',
            dest='netloc',
            action='store',
            default='github.com',
            help='net location of the aip package')

        self.cmd_opts.add_option(
            '-s', '--scheme',
            dest='scheme',
            action='store',
            default='https',
            help='scheme of the aip package')

        # self.cmd_opts.add_option(
        #     '-f', '--froce',
        #     dest='froce',
        #     action='store_true',
        #     default=False,
        #     help='froce download the library')

        self.parser.insert_option_group(0, self.cmd_opts)

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

    def get_archive_url(self, options, package):
       ## parse the url
            package = package.replace('.git', '')
            package_parse = urlparse(package)
            if package_parse.scheme != '':
                scheme = package_parse.scheme   # get scheme
            else:
                scheme = options.scheme
            if package_parse.netloc != '':
                netloc = package_parse.netloc   # get net location
            else:
                netloc = options.netloc

            if "/archive/" in package_parse.path and '.zip' in package_parse.path:  
                path = package_parse.path   # get the path
            else:
                path = package_parse.path + '/archive/master.zip'

            package_url = scheme + '://' + netloc + '/' + path  # form path
            return package_url
          

    def run(self, options, args):
        moduledir = Path(user_data_dir, "modules")
        session = self.get_default_session(options)
        downloader = Downloader(session, progress_bar="on")
        if options.uninstall == True:
            for package in args:
                print(package[package.find("/")+1:])
                if os.path.exists(str(Path(moduledir, package[package.find("/") + 1:]))):
                    shutil.rmtree(
                        str(Path(moduledir, package[package.find("/") + 1:])), onerror=readonly_handler)
                else:
                    print("\033[93m" + package[package.find("/") +
                                               1:] + " not exists\033[0m")
        elif options.list == True:
            print(os.listdir(moduledir))
        else:
            for package in args:
                package_url = self.get_archive_url(options, package)
                package_location = package_url[:package_url.find('/archive')]
                package_location = package_location.split('/')[len(package_location.split('/'))-1]
                package_location = str(Path(moduledir, package_location))   # form location
                if os.path.exists(package_location):    # remove the old package
                    shutil.rmtree(package_location, onerror=readonly_handler)
                link = Link(package_url)

                try:
                    os.makedirs(package_location)
                except OSError as error:
                    print("Directory '%s was exists' " % package_location)
                    print(error)
                    return ERROR

                try:
                    unpack_url(
                        link,
                        package_location,
                        downloader=downloader,
                        download_dir=None,
                    )
                except :
                    print(error)
                    return ERROR

                # downling dependencies
                package_json_location = Path(package_location, 'library.json')
                try:
                    #get library.json from package
                    with open(package_json_location, 'r') as package_json:
                        #get dependencies information from library.json 
                        package_json_dict = json.load(package_json)
                        dependencies = package_json_dict["dependencies"]
                        if len(dependencies) != 0:
                            print("Downloading dependencies......")
                        for dependency in dependencies:
                            print(dependency["name"])
                            dependency_url = self.get_archive_url(options, dependency["url"])
                            dependency_location = package_location + '/' + dependency["name"]
                            try:
                                unpack_url(
                                    Link(dependency_url),
                                    dependency_location,
                                    downloader=downloader,
                                    download_dir=None,
                                )
                            except Exception as error:
                                print(error)
                                return ERROR
                except Exception as error:
                    print("\033[93mBad dependency format, please check library.json\033[0m")
                    print(error)
                    return ERROR


