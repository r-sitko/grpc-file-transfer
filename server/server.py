from concurrent import futures
import logging
import os
import time

import grpc

import protos.file_pb2 as file_pb2
import protos.file_pb2_grpc as file_pb2_grpc

logger = logging.getLogger(__name__)

class FileServicer(file_pb2_grpc.FileServicer):
  _PIECE_SIZE_IN_BYTES = 1024 * 1024 # 1MB

  def __init__(self, files_directory):
    self.__files_directory = files_directory

  def list(self, request, context):
    logger.info("sending files list")
    files = [(f, os.path.getsize(self.__files_directory + "/" + f))
      for f
      in os.listdir(self.__files_directory)
      if os.path.isfile(self.__files_directory + "/" + f)]

    if len(files) == 0:
      yield file_pb2.ListRsp()
    else:
      for file in files:
        yield file_pb2.ListRsp(name=file[0], size=file[1])

  def download(self, request, context):
    file_name = request.name
    if os.path.isfile(self.__files_directory + "/" + file_name):
      logger.info("sending file: {file_name}".format(file_name=file_name))
      with open(self.__files_directory + "/" + file_name, "rb") as fh:
        while True:
          piece = fh.read(FileServicer._PIECE_SIZE_IN_BYTES)
          if len(piece) == 0:
            break
          yield file_pb2.FileDownloadRsp(buffer=piece)
    else:
      error_detail = "File: " + file_name + " not exists"
      logger.error(error_detail)
      context.set_details(error_detail)
      context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
      yield file_pb2.FileDownloadRsp()


class FileServer():
  _ONE_DAY_IN_SECONDS = 60 * 60 * 24

  def __init__(self, ip_address, port, max_workers, files_directory, private_key_file, cert_file):
    self.__ip_address = ip_address
    self.__port = port
    self.__max_workers = max_workers
    self.__files_directory = files_directory
    self.__private_key_file = private_key_file
    self.__cert_file = cert_file

    with open(self.__private_key_file, "rb") as fh:
      private_key = fh.read()
    with open(self.__cert_file, "rb") as fh:
      certificate_chain = fh.read()

    self.__server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.__max_workers))
    file_pb2_grpc.add_FileServicer_to_server(FileServicer(self.__files_directory), self.__server)
    server_credentials = grpc.ssl_server_credentials(((private_key, certificate_chain,),))
    self.__server.add_secure_port(self.__ip_address + ":" + self.__port, server_credentials)

    logger.info("created instance " + str(self))

  def __str__(self):
    return "ip:{ip_address},\
      port:{port},\
      max_workers:{max_workers},\
      files_directory:{files_directory},\
      private_key_file:{private_key_file},\
      cert_file:{cert_file}"\
      .format(
        ip_address=self.__ip_address,
        port=self.__port,
        max_workers=self.__max_workers,
        files_directory=self.__files_directory,
        private_key_file=self.__private_key_file,
        cert_file=self.__cert_file)

  def start(self):
    logger.info("starting instance " + str(self))
    self.__server.start()
    try:
      while True:
        time.sleep(FileServer._ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
      self.__server.stop(0)
