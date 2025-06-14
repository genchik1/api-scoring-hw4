from argparse import ArgumentParser

from src import start_app
from src.settings import set_logging_settings


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()

    set_logging_settings(args.log)

    start_app(args.port)
