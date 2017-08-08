
import os
import logging

env_name = 'INDICATOR_ENV'
if env_name in os.environ:
    ENV = os.environ.get(env_name)
else:
    ENV = 'STAGING'

fmt = "[%(levelname)1.1s] [%(asctime)s %(module)s:%(lineno)d] %(message)s"
log_level = logging.INFO if ENV == 'STAGING' else logging.INFO
logging.basicConfig(level=log_level, format=fmt)

logger = logging.getLogger(__file__)


class Receiver(object):
    if ENV == 'STAGING':
        uri = 'http://127.0.0.1:8086/indicator'
        method = 'POST'
    else:
        uri = 'http://127.0.0.1:8086/indicator'
        method = 'POST'


SDS_INDICATOR_TABLE = dict(
    douban_conv='CL5035/crawl_douban_conv_c3',
    douban_conv_clean='CL5035/douban_conv_clean_c3',
    douban_page_struct='CL5035/crawl_douban_page_struct_c3',
    hw_weibo_conv='CL5035/hw_weibo_conv',
    hw_weibo_conv_clean='CL5035/hw_weibo_conv_clean'
)
