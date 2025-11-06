import argparse
from . import greet, __version__

def main():
    ap = argparse.ArgumentParser(prog="hello")
    ap.add_argument("name")
    ap.add_argument("-V", "--version", action="version", version=__version__)
    args = ap.parse_args()
    print(greet(args.name))
