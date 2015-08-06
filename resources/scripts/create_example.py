#!/bin/python
###############################################################################
# (c) 2005-2015 Copyright, Real-Time Innovations, Inc.  All rights reserved.
# RTI grants Licensee a license to use, modify, compile, and create derivative
# works of the Software.  Licensee has the right to distribute object form only
# for use with RTI products. The Software is provided "as is", with no warranty
# of any type, including any warranty for fitness for any purpose. RTI is under
# no obligation to maintain or support the Software.  RTI shall not be liable
# for any incidental or consequential damages arising out of the use or
# inability to use the software.
###############################################################################

from jinja2 import Template  # It is not compatible with Python3 yet.
from argparse import ArgumentParser
from os import path, makedirs, pardir
from subprocess import check_call, CalledProcessError
from re import match, compile
from shutil import copy

# Automatic IDL generation.
FOO_IDL = """/* Foo IDL generated by create_example.py script. */
struct Foo {
    long a;
};
"""


def copy_file(src, dst, overwrite=False):
    dstfile = dst

    # If it's a folder we will need to join with name.
    # I am not using copy from shutil since I cannot check if I am overwritting
    if path.isdir(dst):
        filename = path.basename(src)
        dstfile = path.join(dst, filename)

    if path.exists(dstfile) and not overwrite:
        return

    copy(src, dstfile)


def copy_files(info):
    # Get IDL file
    regex = compile('.*\.idl')
    info["idlfile"] = [file for file in info["files"] if match(regex, file)]
    info["idlfile"] = info["idlfile"][0] if len(info["idlfile"]) > 0 else None

    # Try to get IDL name if no "--idlname" has been passed
    if info["idlname"] is None:
        if info["idlfile"] is not None:
            info["idlname"] = path.splitext(path.basename(info["idlfile"]))[0]
        else:
            info["idlname"] = info["name"]

    # Copy files
    for f in info["files"]:
        copy_file(f, info["expath"])

    # Update IDL file to take from our example path
    info["idlfile"] = path.join(info["expath"], info["idlname"] + ".idl")

    # Check if IDL file exist and otherwise generate a Foo structure
    if not path.exists(info["idlfile"]):
        with open(info["idlfile"], "w") as idlfile:
            idlfile.write(FOO_IDL)


def call_rtiddsgen(info):
    try:
        # TODO: Check that rtiddsgen is on path or get NDDSHOME env var
        check_call(["rtiddsgen", "-language", info["language"],
                   "-example", info["arch"], info["idlfile"]])
    except CalledProcessError:
        print("Error calling rtiddsgen")


def create_template(info):
    # Get template language.
    template_style = info["language"]
    if template_style in ["c++", "c++03", "c++11"]:
        template_style = "c"

    # Get template file inside "resources" folder with name "readme_x_style.md"
    template_path = path.join(info["repopath"], "resources",
                              "readme_" + template_style + "_style.md")
    with open(template_path, "r") as template_file:
        template_text = template_file.read()

    # Create template
    template = Template(template_text)

    # Write to file the rendered text
    with open(path.join(info["expath"], "README.md"), "w") as readme:
        readme.write(template.render(info))

if __name__ == "__main__":
    # Parse arguments
    parser = ArgumentParser(description='Create structure for new examples.')
    parser.add_argument('name', help='Example short name. This is the name ' +
                        'of the folder that contains it.')
    parser.add_argument('fullname', help='Example long name.')
    parser.add_argument('language', help='Programming language.')
    parser.add_argument('arch', help='Architecture to compile example.')
    parser.add_argument('--idlname', help='The name of the IDL file. ' +
                        'If not specified, "name" will be used.')
    parser.add_argument('files', help='Extra files to copy like IDL. ' +
                        'A Foo IDL file will be created if it is not passed',
                        nargs='*')
    args = parser.parse_args()

    # Create info dictionary with the argument info-
    info = {}
    info["name"] = args.name
    info["fullname"] = args.fullname
    info["language"] = args.language
    info["files"] = args.files
    info["idlname"] = args.idlname
    info["arch"] = args.arch    # Used for rtiddsgen
    info["archwindows"] = "x64Win64VS2013"   # It works for all languages.
    info["archlinux"] = "x64Linux3gcc4.8.2"  # It works for all languages.
    info["scriptpath"] = path.dirname(path.realpath(__file__))
    info["repopath"] = path.join(info["scriptpath"], pardir, pardir)
    info["expath"] = path.join(info["repopath"], "examples", args.name,
                               args.language)

    # Create example directory if it does not exists
    if not path.exists(info["expath"]):
        makedirs(info["expath"])

    # Copy files
    copy_files(info)

    # Create README templates
    create_template(info)

    # Call rtiddsgen to generate files
    call_rtiddsgen(info)
