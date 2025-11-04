#!/usr/bin/env python3

"""
python_package_tree.py is a  free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later
version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
"""

import os
import sys
import ast
from asciitree import LeftAligned  # type: ignore
from asciitree.drawing import BoxStyle, BOX_LIGHT  # type: ignore
import click  # type: ignore


class Parentage(ast.NodeTransformer):
    # current parent (module)
    parent = None

    def __init__(self, no_colorize=False, no_lineno=False):
        self.no_colorize = no_colorize
        self.no_lineno = no_lineno

    def visit(self, node):
        # set parent attribute for this node
        node.parent = self.parent
        # This node becomes the new parent
        self.parent = node

        # Do any work required by super class
        node = super().visit(node)
        # If we have a valid node (ie. node not being removed)
        if isinstance(node, ast.AST):
            # update the parent, since this may have been transformed
            # to a different node by super
            self.parent = node.parent

        if isinstance(node, ast.ClassDef):
            nodeName = (
                node.name
                if self.no_colorize
                else Colors.colorize_text(node.name, "cyan")
            )
            nodeName = nodeName\
                if self.no_lineno\
                else f"{nodeName}:{node.lineno}"
            node.name = nodeName

        if isinstance(node, ast.FunctionDef):
            node.name = node.name\
                if self.no_lineno\
                else f"{node.name}:{node.lineno}"

        return node


class Visitor(ast.NodeVisitor):

    global filename

    def __init__(self):
        self.tree = {}

    def visit(self, node):

        if isinstance(node, ast.ClassDef) or isinstance(node, ast.FunctionDef):
            if isinstance(node, ast.If):
                node.name = "If"
            parents = self.lineage(node)
            if "If" in parents:
                del parents[parents.index("If")]
            search = self.get_nested(self.tree, parents)
            if isinstance(node.parent, ast.Module):
                self.tree[node.name] = {}
            else:
                # Modify self.tree
                try:
                    search[node.name] = {}
                except TypeError:
                    """
                    print(f'''
{filename} {node.name}: {node.lineno}\n\tdef or class definition \
in a control-flow block (if-for-while)
                          ''')
                    """
                    self.tree[node.name] = {}
        self.generic_visit(node)
        return self.tree

    # https://stackoverflow.com/questions/10399614/accessing-value-inside-nested-dictionaries
    def get_nested(self, data, args):
        if args and data:
            element = args[0]
            if element:
                value = data.get(element)
                return value\
                    if len(args) == 1\
                    else self.get_nested(value, args[1:])

    def lineage(self, node):
        np = node.parent
        if isinstance(np, ast.If):
            node.parent.name = "If"
        try:
            lin = [node.parent.name]
        except AttributeError:
            lin = []

        while not isinstance(np, ast.Module):
            np = np.parent
            try:
                lin.append(np.name)
            except AttributeError:
                pass
        return list(reversed(lin))[:]


class Colors:

    colors = {
        "purple": "\033[95m",
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "black": "\033[30m",
        "white": "\033[37m",
    }

    def colorize_text(text, color):
        return f"{Colors.colors[color]}{text}\033[0m"


# Recursive count keys of dictionnary
def count_keys(dict_, counter=0):
    for each_key in dict_:
        if isinstance(dict_[each_key], dict):
            # Recursive call
            counter = count_keys(dict_[each_key], counter + 1)
        else:
            counter += 1
    return counter


# Create a hierarchical data structure of files and directories
# for asciitree
def list_files_recursive(
    path=".", exclude_list=None, no_recursion=False,
    no_colorize=None, no_lineno=None
):
    global filename
    file_info_dict = {}
    for root, dirs, files in os.walk(path):
        cont = False
        for dirname in root.split(os.path.sep):
            if dirname == ".":
                dirname = os.path.basename(os.getcwd())
            if dirname in exclude_list:
                cont = True
                continue

            if cont:
                continue
        if cont:
            continue
        for filename in files:
            if filename.startswith("."):
                continue
            if not filename.endswith(".py"):
                continue
            fname = filename if root == "." else f"{root[2:]}/{filename}"
            fname = fname\
                if no_colorize\
                else Colors.colorize_text(fname, "green")

            with open(f"{root}/{filename}", "r") as fp:
                try:
                    tree = ast.parse(fp.read())
                except Exception as e:
                    input(f"{filename}, {e}")
                # tree = ast.parse(fp.read())
                tree = Parentage(no_colorize=no_colorize,
                                 no_lineno=no_lineno).visit(tree)
                cl = Visitor()
                file_info_dict.update({fname: cl.visit(tree)})

        if no_recursion:
            break

    return file_info_dict


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("path", required=False, default=None)
@click.option(
    "--exclude_dir",
    required=False,
    default=None,
    help="""Comma separated (WITHOUT spaces) list of directory names
              to exclude, default=None""",
)
@click.option(
    "-o", "--outfile", required=False, default=None,
    help="Output file name, default=None"
)
@click.option(
    "--no_recursion",
    "-nr",
    is_flag=True,
    required=False,
    default=None,
    help="Do not explore directories",
)
@click.option(
    "--no_colorize",
    "-nc",
    is_flag=True,
    required=False,
    default=None,
    help="Do not colorize classes and filenames",
)
@click.option(
    "--no_lineno",
    "-nl",
    is_flag=True,
    required=False,
    default=None,
    help="""Do not print line number of
              classes and functions""",
)
def main(path, exclude_dir, outfile, no_recursion, no_colorize, no_lineno):
    """
    Tree-like display of directories, files, classes and functions of
    a python project. The argument PATH may be a dirname or a filename.\n
    Without argument, explore from current directory
    """
    global filename
    if outfile:
        no_colorize = True

    if not path:
        path = "."
    exclude_list = ["__pycache__", "yap.egg-info", ".git"]
    try:
        exclude_list += exclude_dir.split(",")
    except AttributeError:
        pass

    if os.path.isfile(path):
        if not path.endswith(".py"):
            sys.exit("\tI only handle .py files")
        filename = path
        with open(path, "r", encoding="utf-8") as fp:
            tree = ast.parse(fp.read())
            tree = Parentage(no_colorize=no_colorize,
                             no_lineno=no_lineno).visit(tree)
            path = path if no_colorize else Colors.colorize_text(path, "green")
            tree_dict = {path: Visitor().visit(tree)}

    else:
        file_info_dict = list_files_recursive(
            path=path,
            exclude_list=exclude_list,
            no_recursion=no_recursion,
            no_colorize=no_colorize,
            no_lineno=no_lineno,
        )
        path = os.path.basename(os.getcwd()) if path == "." else path
        tree_dict = {path: file_info_dict}

    if count_keys(tree_dict) > 1000 and not outfile:
        sys.exit(
            f"""Very long output ({count_keys(tree_dict)} lines),
                 may no fit in terminal, \nUse:\n
                 python_package_tree -o python_package_tree.output"""
        )
    box_tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=3, indent=3))
    if tree_dict:
        if outfile:
            with open(outfile, "w") as out_h:
                print(box_tr(tree_dict), file=out_h)
        else:
            print(box_tr(tree_dict))


if __name__ == "__main__":
    main()
