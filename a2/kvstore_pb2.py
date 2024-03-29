# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: kvstore.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='kvstore.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\rkvstore.proto\"\x10\n\x02Id\x12\n\n\x02id\x18\x01 \x01(\t\"6\n\tDataBlock\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x0c\x12\r\n\x05\x65rror\x18\x03 \x01(\x08\"\x1c\n\nSaveStatus\x12\x0e\n\x06status\x18\x01 \x01(\t2L\n\rKeyValueStore\x12!\n\x04Save\x12\n.DataBlock\x1a\x0b.SaveStatus\"\x00\x12\x18\n\x03Get\x12\x03.Id\x1a\n.DataBlock\"\x00\x62\x06proto3')
)




_ID = _descriptor.Descriptor(
  name='Id',
  full_name='Id',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='Id.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=17,
  serialized_end=33,
)


_DATABLOCK = _descriptor.Descriptor(
  name='DataBlock',
  full_name='DataBlock',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='DataBlock.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='DataBlock.value', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='error', full_name='DataBlock.error', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=35,
  serialized_end=89,
)


_SAVESTATUS = _descriptor.Descriptor(
  name='SaveStatus',
  full_name='SaveStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SaveStatus.status', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=91,
  serialized_end=119,
)

DESCRIPTOR.message_types_by_name['Id'] = _ID
DESCRIPTOR.message_types_by_name['DataBlock'] = _DATABLOCK
DESCRIPTOR.message_types_by_name['SaveStatus'] = _SAVESTATUS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Id = _reflection.GeneratedProtocolMessageType('Id', (_message.Message,), {
  'DESCRIPTOR' : _ID,
  '__module__' : 'kvstore_pb2'
  # @@protoc_insertion_point(class_scope:Id)
  })
_sym_db.RegisterMessage(Id)

DataBlock = _reflection.GeneratedProtocolMessageType('DataBlock', (_message.Message,), {
  'DESCRIPTOR' : _DATABLOCK,
  '__module__' : 'kvstore_pb2'
  # @@protoc_insertion_point(class_scope:DataBlock)
  })
_sym_db.RegisterMessage(DataBlock)

SaveStatus = _reflection.GeneratedProtocolMessageType('SaveStatus', (_message.Message,), {
  'DESCRIPTOR' : _SAVESTATUS,
  '__module__' : 'kvstore_pb2'
  # @@protoc_insertion_point(class_scope:SaveStatus)
  })
_sym_db.RegisterMessage(SaveStatus)



_KEYVALUESTORE = _descriptor.ServiceDescriptor(
  name='KeyValueStore',
  full_name='KeyValueStore',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=121,
  serialized_end=197,
  methods=[
  _descriptor.MethodDescriptor(
    name='Save',
    full_name='KeyValueStore.Save',
    index=0,
    containing_service=None,
    input_type=_DATABLOCK,
    output_type=_SAVESTATUS,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='Get',
    full_name='KeyValueStore.Get',
    index=1,
    containing_service=None,
    input_type=_ID,
    output_type=_DATABLOCK,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_KEYVALUESTORE)

DESCRIPTOR.services_by_name['KeyValueStore'] = _KEYVALUESTORE

# @@protoc_insertion_point(module_scope)
