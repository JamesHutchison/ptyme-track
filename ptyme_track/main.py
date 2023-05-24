import argparse
import logging

from ptyme_track.cement import cement_cur_times
from ptyme_track.client import PtymeClient, StandalonePtymeClient
from ptyme_track.ptyme_env import SERVER_URL

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="ptyme_track")
    parser.add_argument(
        "--generate-secret", action="store_true", help="Generate a secret and update gitignore"
    )
    parser.add_argument("--server", action="store_true", help="Run as server")
    parser.add_argument("--client", action="store_true", help="Run as client")
    # cement takes a parameter which is the name of the file to cement to
    parser.add_argument("--cement", help="Cement to file")

    args = parser.parse_args()

    if args.server:
        from ptyme_track.server import run_forever

        run_forever()
    if args.cement:
        cement_cur_times(args.cement)
        return
    if args.generate_secret:
        from ptyme_track.server import generate_secret

        generate_secret()
        return
    if args.client:
        client = PtymeClient(SERVER_URL)
    else:
        client = StandalonePtymeClient()
    client.prep_ptyme_dir()
    client.run_forever()


if __name__ == "__main__":
    main()
