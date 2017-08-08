namespace java com.xiaomi.oakbay.thrift

include "LindenCommon.thrift"

struct Response {
    1:required bool success = 1,
    2:optional string error,
}

struct OakbaySearchResult {
    1: required bool success,
    2: optional string error,
    3: optional LindenCommon.LindenResult lindenResult,
}

service OakbayClientService {
    OakbaySearchResult handleBqlRequest(1: string domain, 2: string cluster, 3: string bql);
    Response handleIndexRequest(1: string domain, 2: string cluster, 3: list<string> contents);
    OakbaySearchResult handleTemplatedBqlRequest(1: string domain, 2: string cluster, 3: string template, 4: string bql);
}