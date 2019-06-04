import argparse
import logging
import sys

from client.client import FileClient

def main():
  log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  logging.basicConfig(level=logging.INFO, format=log_fmt)
  logger = logging.getLogger(__name__)

  parser = argparse.ArgumentParser(description="gRPC file transfer client")
  parser.add_argument(
    "-i", "--ip_adress", required=True, type=str, help="IP address of server")
  parser.add_argument(
    "-p", "--port", required=True, type=str, help="port address of server")
  parser.add_argument(
    "-c", "--cert_file", required=True, type=str, help="certificate file path")

  subparsers = parser.add_subparsers(dest="action", help="client possible actions")
  subparsers.required = True

  download_parser = subparsers.add_parser("download", help="download file from server")
  download_parser.add_argument(
    "-d", "--directory", required=True, type=str, help="where to save files")
  download_parser.add_argument(
    "-f", "--file", required=True, type=str, help="file name to download")

  subparsers.add_parser("list", help="list files on server")

  args = parser.parse_args()

  logger.info("ip_adress:{ip_adress}, port:{port}, cert_file:{cert_file}, action:{action}"
    .format(
      ip_adress=args.ip_adress,
      port=args.port,
      cert_file=args.cert_file,
      action=args.action))

  client = FileClient(args.ip_adress, args.port, args.cert_file)

  action = args.action
  if action == "download":
    client.download(args.file, args.file, args.directory)
  elif action == "list":
    client.list()
  else:
    logger.error("no such action " + action)

if __name__ == "__main__":
  main()
