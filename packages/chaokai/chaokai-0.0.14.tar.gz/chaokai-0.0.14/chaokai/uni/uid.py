# -*- coding: utf-8 -*-
import datetime
import time
import uuid


def create_uuid(first_str='', length=10, is_upper=False):
    """
    生成uuid
    """
    uuid4 = str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')
    resp_str = str(first_str) + uuid4[:length]

    if is_upper:
        resp_str = resp_str.upper()

    return resp_str


def create_date_id(prefix='', suffix=''):
    """

    :param length: 长充
    :param prefix: 前缀
    :param suffix: 后缀
    :return: 20位时间ID
    """
    """
    生成基于时间的数字id
    """
    date_str = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))

    return prefix + date_str + suffix



if __name__ == '__main__':
    r = create_uuid()
    print(len(r), '--', r)

    r = create_date_id()
    print(r, len(r))

