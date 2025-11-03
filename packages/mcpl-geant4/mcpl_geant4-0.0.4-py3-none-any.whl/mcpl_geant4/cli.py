
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################

def parse_args():
    from argparse import ArgumentParser, RawTextHelpFormatter
    import textwrap
    def wrap(t,w=59):
        return textwrap.fill( ' '.join(t.split()), width=w )

    descr = """Get information about NCrystalGeant4 installation."""
    parser = ArgumentParser( description=wrap(descr,79),
                             formatter_class = RawTextHelpFormatter )
    from . import __version__ as progversion
    parser.add_argument('--version', action='version', version=progversion)

    parser.add_argument('--cmakedir', action='store_true',
                        help=wrap(
                            """Print the directory in which
                            NCrystalGeant4Config.cmake resides. To make a CMake
                            project with find_package(NCrystalGeant4) work, the
                            printed directory must either be added to the
                            CMAKE_PREFIX_PATH, or the variable
                            NCrystalGeant4_DIR can be set to the value.""" )
                        )
    parser.add_argument('--includedir', action='store_true',
                        help=wrap(
                            """Print the directory in which NCrystalGeant4
                            header files reside (for advanced users wishing to
                            modify include paths manually).""" )
                        )
    parser.add_argument('--srcdir', action='store_true',
                        help=wrap(
                            """Print the directory in which NCrystalGeant4
                            source files reside (for advanced users wishing to
                            process them manually).""" )
                        )

    args = parser.parse_args()

    nselect = sum( (1 if e else 0)
                   for e in (args.cmakedir,args.includedir,args.srcdir) )
    if nselect == 0:
        parser.error('Invalid usage. Run with -h/--help for instructions.')
    if nselect > 1:
        parser.error('Conflicting options')
    return args

def main():
    import pathlib
    cmakedir = pathlib.Path(__file__).parent.joinpath('cmake').absolute()
    args = parse_args()
    if args.cmakedir:
        print( cmakedir )
    elif args.includedir:
        print( cmakedir.joinpath('include') )
    elif args.srcdir:
        print( cmakedir.joinpath('src') )
    else:
        assert False, "Implementation error"
