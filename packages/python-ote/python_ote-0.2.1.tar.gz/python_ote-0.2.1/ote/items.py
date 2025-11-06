# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from datetime import time
import locale
import re

import scrapy
from itemloaders.processors import TakeFirst


def parse_time(values):
    for value in values:
        # Expecting a time interval string like this: "04:15-04:30"
        match = re.match(r'(\d\d):(\d\d)-(\d\d):(\d\d)', value)
        if match is not None:
            yield time(int(match[1]), int(match[2]))


def parse_price(values):
    locale.setlocale(locale.LC_NUMERIC, 'cs_CZ.UTF-8')
    return [locale.atof(value.replace(' ', '')) for value in values]


class DayMarketPricesItem(scrapy.Item):
    date = scrapy.Field(output_processor=TakeFirst())
    time = scrapy.Field(input_processor=parse_time, output_processor=TakeFirst())
    price = scrapy.Field(input_processor=parse_price, output_processor=TakeFirst())
