# Repo: https://github.com/e6766817-del/kongfu-chess
import sys

from kfchess.texttests.script_runner import run


def main(stream=sys.stdin):
    run(stream, print)


if __name__ == "__main__":
    main()
