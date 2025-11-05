# -*- coding: utf-8 -*-
import re
from decimal import Decimal


def money_2f(money):
    """保留2位小数"""
    return str(Decimal(money).quantize(Decimal('0.00')))


def count_decimal_places(number):
    """判断金额小数点后有几位"""
    decimal_places = re.search('\.[0-9]*', str(number))
    if decimal_places:
        return len(decimal_places.group(0)) - 1
    else:
        return 0


if __name__ == '__main__':
    r = count_decimal_places(12.3666)
    print(r)