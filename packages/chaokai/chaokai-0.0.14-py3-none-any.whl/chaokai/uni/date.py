# -*- coding: utf-8 -*-
import datetime
import time


def fmt_time(timestamp, status=1):
    """格式化时间戳"""
    try:
        tsp = int(timestamp)
    except:
        return ''

    if tsp == 0:
        return ''

    try:
        if status == 1:
            date = time.strftime('%Y.%m.%d %H:%M', time.localtime(tsp))
        elif status == 2:
            date = time.strftime('%Y.%m.%d', time.localtime(tsp))
        elif status == 3:
            date = time.strftime('%Y/%m/%d', time.localtime(tsp))
        elif status == 4:
            date = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(tsp))
        elif status == 5:
            date = time.strftime('%Y-%m', time.localtime(tsp))
        elif status == 6:
            date = time.strftime('%Y%m%d', time.localtime(tsp))
        elif status == 7:
            date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tsp))
        elif status == 8:
            date = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(tsp))
        elif status == 9:
            date = time.strftime('%Y-%m-%d', time.localtime(tsp))
        else:
            date = time.strftime('%Y.%m.%d', time.localtime(tsp))
    except:
        return '0'

    return date


def excel_to_timestamp(excel_date):
    """
    将 Excel 日期数字转换为 Unix 时间戳（支持 1899-1970 年的日期）
    :param excel_date: Excel 日期（如 44197 代表 2021-01-01）
    :return: Unix 时间戳（秒级，可能为负数）
    """
    # Excel 的基准日期是 1899-12-30（Windows 版本）
    excel_base_date = datetime.datetime(1899, 12, 30)

    # 计算天数差（Excel 日期可能是浮点数，如 44197.75 表示带时间的日期）
    days_since_base = float(excel_date)
    delta = datetime.timedelta(days=days_since_base)

    # 得到目标日期（本地时间）
    target_date = excel_base_date + delta

    # 手动计算 1970-01-01 之前的时间戳（避免 timestamp() 的局限性）
    unix_epoch = datetime.datetime(1970, 1, 1)
    if target_date < unix_epoch:
        # 1970 年之前的日期，计算负时间戳
        time_before_epoch = unix_epoch - target_date
        timestamp = -time_before_epoch.total_seconds()
    else:
        # 1970 年之后的日期，直接使用 timestamp()
        timestamp = target_date.timestamp()

    return int(timestamp)


if __name__ == '__main__':
    r = excel_to_timestamp(43632)
    print(r)
    date_str = fmt_time(r)
    print(date_str)
