#
# Autogenerated by Thrift
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#

from thrift.Thrift import *
import oakbayThrift.LindenCommon
import oakbayThrift.LindenCommon.ttypes


from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TProtocol
try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None



class Response:
  """
  Attributes:
   - success
   - error
  """

  thrift_spec = (
    None, # 0
    (1, TType.BOOL, 'success', None, True, ), # 1
    (2, TType.STRING, 'error', None, None, ), # 2
  )

  def __init__(self, success=thrift_spec[1][4], error=None,):
    self.success = success
    self.error = error

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.BOOL:
          self.success = iprot.readBool();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRING:
          self.error = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Response')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.BOOL, 1)
      oprot.writeBool(self.success)
      oprot.writeFieldEnd()
    if self.error != None:
      oprot.writeFieldBegin('error', TType.STRING, 2)
      oprot.writeString(self.error)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      if self.success is None:
        raise TProtocol.TProtocolException(message='Required field success is unset!')
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class OakbaySearchResult:
  """
  Attributes:
   - success
   - error
   - lindenResult
  """

  thrift_spec = (
    None, # 0
    (1, TType.BOOL, 'success', None, None, ), # 1
    (2, TType.STRING, 'error', None, None, ), # 2
    (3, TType.STRUCT, 'lindenResult', (oakbayThrift.LindenCommon.ttypes.LindenResult, oakbayThrift.LindenCommon.ttypes.LindenResult.thrift_spec), None, ), # 3
  )

  def __init__(self, success=None, error=None, lindenResult=None,):
    self.success = success
    self.error = error
    self.lindenResult = lindenResult

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.BOOL:
          self.success = iprot.readBool();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRING:
          self.error = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.STRUCT:
          self.lindenResult = oakbayThrift.LindenCommon.ttypes.LindenResult()
          self.lindenResult.read(iprot)
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('OakbaySearchResult')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.BOOL, 1)
      oprot.writeBool(self.success)
      oprot.writeFieldEnd()
    if self.error != None:
      oprot.writeFieldBegin('error', TType.STRING, 2)
      oprot.writeString(self.error)
      oprot.writeFieldEnd()
    if self.lindenResult != None:
      oprot.writeFieldBegin('lindenResult', TType.STRUCT, 3)
      self.lindenResult.write(oprot)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      if self.success is None:
        raise TProtocol.TProtocolException(message='Required field success is unset!')
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)
