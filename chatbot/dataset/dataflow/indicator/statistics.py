import datetime

from helper.sds_helper import SDSHelper
from comm.config import SDSConfig
from comm import tmtool

from config import SDS_INDICATOR_TABLE


class Statistics(object):
    def __init__(self):
        self.sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret, SDSConfig.chatbot_sds_endpoint)
        self._table_name = SDSConfig.chatbot_statistic_table_name
        self._map_table = SDS_INDICATOR_TABLE

    def _get_count(self, ds, name):
        res = self.sds.get(self._table_name,
                           keys={
                               'time': ds,
                               'name': name
                           })
        if res is None:
            return None
        else:
            return res['count']

    def _scan_one_day(self, ds):
        res = []
        for r in self.sds.scan(self._table_name,
                               start_key={'time': ds},
                               stop_key={'time': ds}):
            res.append(r)

    def _one_day_indicator(self, date):
        ds = tmtool.date_ds(date)
        res = []
        for name, row_name in self._map_table.iteritems():
            count = self._get_count(ds, row_name)
            if count is not None:
                res.append([name, count])
        return res

    def one_day_indicator(self, date):
        if isinstance(date, datetime.date):
            pass
        elif isinstance(date, str):
            dt = datetime.datetime.strptime(date, tmtool.date_fmt)
            date = dt.date()
        else:
            raise Exception('Value Type Error: Not date or str')

        date_str = date.strftime(tmtool.date_fmt)

        name_counts = self._one_day_indicator(date)
        indicators = map(lambda x: dict(type='date', name=x[0], count=x[1], time=date_str), name_counts)

        return indicators


if __name__ == '__main__':
    indicator = Statistics()
    print indicator.one_day_indicator(datetime.date.today())
