"""
@author axiner
@version v0.0.1
@created 2025/10/20 14:50
@abstract
@description
@history
"""
import argparse
import sys

from toollib.pyd import PydPacker

from pydpack import __version__

prog = "pydpack"


def main():
    parser = argparse.ArgumentParser(
        prog=prog,
        description="This is a pydpack.（pyd打包，可将py目录或文件打包成pyd(so)）",
        epilog="examples: \n"
               "  %(prog)s -s <py目录或文件> -e main.py\n"
               "",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}")
    parser.add_argument(
        '-s',
        '--src',
        required=True,
        type=str,
        metavar="",
        help='源（py目录或文件）')
    parser.add_argument(
        '-e',
        '--exclude',
        type=str,
        metavar="",
        help='排除编译（正则表达式，使用管道等注意加引号）')
    parser.add_argument(
        '-i',
        '--ignore',
        default='.git|.idea|.vscode|__pycache__',
        type=str,
        metavar="",
        help='忽略复制（正则表达式，使用管道等注意加引号）')
    parser.add_argument(
        '--ext-suffix',
        action='store_true',
        help='是否保留扩展后缀（默认不保留）')
    parser.add_argument(
        '--clean',
        action='store_true',
        help='是否清理（默认不清理）')
    args = parser.parse_args()
    src = args.src.strip()
    if not src or src == "''":
        sys.stderr.write('ERROR: -s/--src: 不能为空\n')
        sys.exit(1)
    packer = PydPacker(
        src=src,
        exclude=args.exclude,
        ignore=args.ignore,
        keep_ext_suffix=args.ext_suffix,
        is_clean=args.clean,
    )
    packer.run()


if __name__ == "__main__":
    main()
