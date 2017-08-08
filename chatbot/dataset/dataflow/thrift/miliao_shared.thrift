/**
 *
 */

namespace java com.xiaomi.miliao.thrift
namespace cpp  com.xiaomi.miliao.thrift

/**
 * This a base service for all Miliao Thrift Service. All other services should extend this service.
 */
service MiliaoSharedService {
   /**
    * Returns a descriptive name of the service
    */
   string getName(),

   /**
    * Gets the counters for this service
    */
   map<string, i64> getCounters(),

   /**
    * Gets the counters start with prefix for this service
    */
   map<string, i64> getCountersByCategory(1: string prefix),

   /**
    * Gets the counters start with prefixs for this service
    */
   map<string, i64> getCountersByCategories(1: list<string> prefixes),

   /**
    * Gets the names of counters for this service
    */
   list<string> getCounterNames(),

   /**
    * Gets the value of a single counter
    */
   i64 getCounter(1: string key),
   
   /**
    * Returns the unix time that the server has been running since
    */
   i64 aliveSince(),

   /**
    * Suggest a stop to the server
    */
   oneway void shutdown(),
}
