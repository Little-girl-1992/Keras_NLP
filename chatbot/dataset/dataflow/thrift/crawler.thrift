namespace java com.xiaomi.micrawler.thrift

include "miliao_shared.thrift"

struct TaskRequest {
    1: required set<string> urls,
    2: required string businessName,
    3: required string taskTag
}

struct TaskResponse {
    1: required bool success,
    2: optional string error,
}

service CrawlerService extends miliao_shared.MiliaoSharedService{
    TaskResponse submitTask(1: TaskRequest request);
}