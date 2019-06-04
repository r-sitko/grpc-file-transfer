import logging
import os
import time

import grpc

import protos.file_pb2 as file_pb2
import protos.file_pb2_grpc as file_pb2_grpc

logger = logging.getLogger(__name__)

class FileClient:
  def __init__(self, ip_address, port, cert_file):
    self.__ip_address = ip_address
    self.__port = port
    self.__cert_file = cert_file

    with open(self.__cert_file, "rb") as fh:
      trusted_cert = fh.read()

    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_cert)
    channel = grpc.secure_channel("{}:{}"
      .format(self.__ip_address, self.__port), credentials)
    self.stub = file_pb2_grpc.FileStub(channel)

    logger.info("created instance " + str(self))

  def list(self):
    logger.info("downloading files list from server")
    response_stream = self.stub.list(file_pb2.ListReq())
    self.__list_files(response_stream)

  def download(self, file_name, out_file_name, out_file_dir):
    logger.info("downloading file:{file_name} to {out_file_dir}/{out_file_name}"
      .format(
        file_name=file_name,
        out_file_dir=out_file_dir,
        out_file_name=out_file_name))
    response_stream = self.stub.download(file_pb2.FileDownloadReq(name=file_name))
    self.__download_file(response_stream, out_file_name, out_file_dir)

  def __download_file(self, response_stream, out_file_name, out_file_dir):
    try:
      with open(out_file_dir + "/" + out_file_name, "wb") as fh:
          for response in response_stream:
            fh.write(response.buffer)
    except grpc.RpcError as e:
      status_code = e.code()
      logger.error("Error details: {}, status name: {}, status value: {}"
        .format(e.details(), status_code.name, status_code.value))

  def __list_files(self, response_stream):
    for response in response_stream:
      print("file name: {}, size: {} bytes".format(response.name, response.size))

  def __str__(self):
    return "ip:{ip_address}, port:{port}, cert_file:{cert_file}"\
      .format(
        ip_address=self.__ip_address,
        port=self.__port,
        cert_file=self.__cert_file)
