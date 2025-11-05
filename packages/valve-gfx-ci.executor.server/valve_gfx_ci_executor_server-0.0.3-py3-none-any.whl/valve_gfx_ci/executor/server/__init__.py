import argparse
import sys


# Entrypoint for the executor script
def run():
    parser = argparse.ArgumentParser(prog='Executor Server')
    subparsers = parser.add_subparsers(help='Desired action to perform. Default: server', dest='action')

    # Server
    subparsers.add_parser("server", help='Start running the executor as a server')

    # Run-job
    parser_job = subparsers.add_parser("run-job", help='Start running a job')
    parser_job.add_argument('-c', '--config', type=argparse.FileType('r'), default=sys.stdin,
                            help="The job description to execute")
    parser_job.add_argument('-s', '--socket', required=True,
                            help="Path to the unix socket to use to communicate")
    parser_job.add_argument('-l', '--lock-file', required=True,
                            help="Path to the lock file to use")

    # Parse the command line
    args = parser.parse_args()

    # Execute the right entrypoint
    if args.action is None or args.action == "server":
        from .app import run
        run()
    elif args.action == "run-job":
        from .executor import run
        run(config_f=args.config, socket_path=args.socket, lock_path=args.lock_file)
