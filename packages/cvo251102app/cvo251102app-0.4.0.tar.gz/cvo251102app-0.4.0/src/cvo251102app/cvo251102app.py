import sys

from cvo251102lib import hello


def main() -> None:
    if len(sys.argv) > 1:
        print(hello(someone=sys.argv[1]))
    else:
        print(hello())
