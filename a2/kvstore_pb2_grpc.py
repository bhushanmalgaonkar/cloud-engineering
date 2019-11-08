# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import kvstore_pb2 as kvstore__pb2


class KeyValueStoreStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Save = channel.unary_unary(
        '/KeyValueStore/Save',
        request_serializer=kvstore__pb2.DataBlock.SerializeToString,
        response_deserializer=kvstore__pb2.SaveStatus.FromString,
        )
    self.Get = channel.unary_unary(
        '/KeyValueStore/Get',
        request_serializer=kvstore__pb2.Id.SerializeToString,
        response_deserializer=kvstore__pb2.DataBlock.FromString,
        )


class KeyValueStoreServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def Save(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def Get(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_KeyValueStoreServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Save': grpc.unary_unary_rpc_method_handler(
          servicer.Save,
          request_deserializer=kvstore__pb2.DataBlock.FromString,
          response_serializer=kvstore__pb2.SaveStatus.SerializeToString,
      ),
      'Get': grpc.unary_unary_rpc_method_handler(
          servicer.Get,
          request_deserializer=kvstore__pb2.Id.FromString,
          response_serializer=kvstore__pb2.DataBlock.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'KeyValueStore', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
