# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import mapreduce_pb2 as mapreduce__pb2


class MapReduceMasterStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.SubmitJob = channel.unary_stream(
        '/MapReduceMaster/SubmitJob',
        request_serializer=mapreduce__pb2.Job.SerializeToString,
        response_deserializer=mapreduce__pb2.ExecutionInfo.FromString,
        )


class MapReduceMasterServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def SubmitJob(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_MapReduceMasterServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'SubmitJob': grpc.unary_stream_rpc_method_handler(
          servicer.SubmitJob,
          request_deserializer=mapreduce__pb2.Job.FromString,
          response_serializer=mapreduce__pb2.ExecutionInfo.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'MapReduceMaster', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))


class MapReduceWorkerStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Execute = channel.unary_unary(
        '/MapReduceWorker/Execute',
        request_serializer=mapreduce__pb2.Task.SerializeToString,
        response_deserializer=mapreduce__pb2.ExecutionInfo.FromString,
        )


class MapReduceWorkerServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def Execute(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_MapReduceWorkerServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Execute': grpc.unary_unary_rpc_method_handler(
          servicer.Execute,
          request_deserializer=mapreduce__pb2.Task.FromString,
          response_serializer=mapreduce__pb2.ExecutionInfo.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'MapReduceWorker', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
