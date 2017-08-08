namespace java com.xiaomi.data.spec.log.micloud

struct ChatbotDoubanGroupPage {
    1:optional string url;//url
    2:optional i64 fetchTime;//fetchTime
    3:optional binary rawData;//原始页面
    4:optional string taskTag;//taskTag
    5:optional string linkinfo;//linkInfo
    6:optional string fdsPath;//fdsPath
}

struct ChatbotDoubanGroupStruct{
    1:optional i64 topicId;//topic id
    2:optional string url;//url
    3:optional i64 updateTime;//update time
    4:optional binary rawData;//json
    5:optional i64 thisPage;//this page number
    6:optional i64 totalPage;//total page number
}