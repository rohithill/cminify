#!/usr/bin/env python2.7
#     C Minify Copyright (C) 2015 Alexandre Baron
#     This program comes with ABSOLUTELY NO WARRANTY; for details read LICENSE.
#     This is free software, and you are welcome to redistribute it
#     under certain conditions; read LICENSE for details.

import argparse
import sys
import re
import os  # SEEK_END etc.

# Ops: ops that may be spaced out in the code but we can trim the whitespace
# special ops are the same but for ops that may be mistaken for regex control characters so they are espaced
# Spaced ops are ops that are defined in the C language to be delimited by spaces (keywords most of the time)
OPS = ['+', '-', '*', '/', '+=', '-=', '*=', '/=', '=', '<', '>', '<=', '>=', ',', '(', ')', '{', '}', ';']
SPECIAL_OPS = ['+', '*', '+=', '*=', '(', ')']
SPACED_OPS = ['else']


def remove_everything_between(subs1, subs2, line):
    regex = re.compile(subs1 + r'.*' + subs2)
    return regex.sub('', line)


def remove_everything_before(subs, line):
    regex = re.compile(r'.*' + subs)
    return regex.sub('', line)


def remove_everything_past(subs, line):
    regex = re.compile(subs + r'.*')
    return regex.sub('', line)


def remove_multiline_comments(lines):
    start, end = '/*', '*/'
    escaped_start, escaped_end = '/\*', '\*/'
    in_comment = False
    newlines = []
    for line in lines:
        if not in_comment:
            start_pos = line.find(start)
            if start_pos != -1:
                in_comment = True
                end_pos = line.find(end)
                # inline multiline comment
                if start_pos < end_pos:
                    line = remove_everything_between(escaped_start, escaped_end, line)
                    in_comment = False
                else:
                    line = remove_everything_past(escaped_start, line)
        else:
            end_pos = line.find(end)
            if end_pos != -1:
                line = remove_everything_before(escaped_end, line)
                in_comment = False
                start_pos = line.find(start)
                # start of another comment on the same line
                if start_pos != -1:
                    line = remove_everything_past(escaped_start, line)
                    in_comment = True
            else:
                line = ''
        newlines.append(line)
    return newlines


def remove_inline_comments(lines):
    return map(lambda x: remove_everything_past('//', x), lines)


def trim(lines):
    """Removes all leading and trailing whitespace characters for all lines"""
    return map(lambda x: x.strip(), lines)


def minify_operator(op):
    """Returns a function applying a regex to strip away spaces on each side of an operator
    Makes a special escape for operators that could be mistaken for regex control characters."""
    to_compile = r' *'
    if op in SPECIAL_OPS:
        to_compile += "\\"
    to_compile += op + r" *"
    regex = re.compile(to_compile)
    return lambda string: regex.sub(op, string)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', help="Input files")
    parser.add_argument("-c", "--crlf",
                        help="Use CRLF as newline control character (\r\n)",
                        default='\n',
                        action='store_const', const='\r\n')
    parser.add_argument("-n", "--names",
                        help="Show name of processed files",
                        action='store_true')
    parser.add_argument("-s", "--stats",
                        help="Show statistics on minified version",
                        action='store_true')
    parser.add_argument("-m", "--keep-multiline",
                        help="Don't strip multiline comments (/* ... */)",
                        action='store_true')
    parser.add_argument("-i", "--keep-inline",
                        help="Do not strip inline comments (// ...)",
                        action='store_true')
    parser.add_argument("-w", "--keep-newline",
                        help="Keep newline control characters",
                        action='store_true')
    args = parser.parse_args()
    return args


def show_stats(source_file, minified_text):
    # After "f.readlines", the file pointer is at file's end so tell() will return current file size.
    orig_size = source_file.tell()
    mini_size = len(minified_text)
    delta = orig_size - mini_size
    print(
        "Original: {0} characters, Minified: {1} characters, {2} removed ({3:.1f}%)"
        .format(orig_size, mini_size, delta, (float(delta) / float(orig_size)) * 100.0)
    )


def minify_source_file(args, filename):
    newline = args.crlf
    with open(filename) as f:
        if args.names is True:
            print("File {}:".format(source_file))
        lines = f.readlines()
        if args.keep_newline is False:
            # Keep preprocessor lines (starting with #)
            lines = map(lambda x: x.replace(newline, '') if not x.startswith('#') else x, lines)
        lines = map(lambda x: x.replace('\t', ' '), lines)
        # for each operator: remove space on each side of the op, on every line.
        # Escape ops that could be regex control characters.
        for op in OPS:
            lines = map(minify_operator(op), lines)
        # If it's a spaced op, do the contrary: ensure it is spaced out before and after.
        for op in SPACED_OPS:
            lines = map(space_operator(op), lines)
        lines = trim(lines)  # erase leading and trailing whitespace
        if args.keep_inline is False:
            lines = remove_inline_comments(lines)
        if args.keep_multiline is False:
            lines = remove_multiline_comments(lines)
        # Finally convert all remaining multispaces to single spaces
        multi_spaces = re.compile(r'[  ]+ *')
        lines = map(lambda string: multi_spaces.sub(' ', string), lines)
        minified = ''.join(lines)
        print(minified)
        if args.stats is True:
            show_stats(f, minified)


def main():
    args = get_args()

    for filename in args.files:
        minify_source_file(args, filename)

if __name__ == "__main__":
    main()
