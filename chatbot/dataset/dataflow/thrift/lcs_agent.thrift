namespace java com.xiaomi.infra.galaxy.lcs.thrift

enum ErrorCode {
  SUCCESS = 0,
  UNEXCEPTED_ERROR = 1,
  BUFFER_FULL = 2,
  DESERIALIZE_FAILED = 3,
  FILE_NOT_EXIST = 4,
  IO_ERROR = 5,
  TALOS_OPERATION_FAILED = 6,
  INVALID_TOPIC = 7,
  AGENT_NOT_READY = 8,
  MODULED_STOPED = 9,
  TOO_MANY_FILES = 10,
  SERIALIZE_FAILED = 11,
  THRIFT_TRANSPORT_FAILED = 12,

  OPERATION_FAILED = 100,
  HBASE_OPERATION_FAILED = 101,
  TEAM_EXIST = 102,
  TEAM_NOT_EXIST = 103,
  VERSION_CONFLICTING_ERROR = 104,
  MODULE_EXIST = 105,
  MODULE_NOT_EXIST = 106,
  INVALID_REQUEST_PARAMS = 107,
  UNKNOW_TALOS_CLUSTER = 108,
  LINK_UNIT_KEY_NOT_EXIST = 109,
  PERMISSION_DENIED = 110,

}

exception GalaxyLCSException {
  1: required ErrorCode errorCode;

  2: optional string errMsg;

  3: optional string details;
}


struct Record {
  1: required string clusterName;
  2: required string orgId;
  3: required string topicName;
  4: required string teamId;
  5: required list<binary> data;
  6: optional bool extendAgentData = false;
}

service LCSAgentService {
  void Record(1: Record record) throws (1: GalaxyLCSException e);
}