import sys

from cvo251102app import hello


def main() -> None:
    if len(sys.argv) > 1:
        print(hello(someone=sys.argv[1]))
    else:
        print(hello())


if __name__ == "__main__":
    main()
