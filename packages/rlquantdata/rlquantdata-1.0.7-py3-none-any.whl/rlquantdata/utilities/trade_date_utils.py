import os

import pandas as pd

import rlquantdata.DateUtilities.Calendar
import rlquantdata.DateUtilities.DateUtilities as pai
from rlquantdata.DateUtilities import Date
from rlquantdata.DateUtilities.Date_enum import BizDayConventions, DateGeneration
from rlquantdata.client import BaseClient


class TradeDateUtils:
    def __init__(self, trade_path=None, client: BaseClient = None):
        if trade_path is not None and os.path.exists(trade_path):
            trade_date = pd.read_feather(trade_path).set_index('trade_date')
            biz_data = trade_date['001002'].astype(bool)
            true_indexes = pd.to_datetime(biz_data.index[~biz_data.values])
            hk_biz_data = trade_date['002001'].astype(bool)
            hk_true_indexes = pd.to_datetime(hk_biz_data.index[~hk_biz_data.values])
            us_biz_data = trade_date['101001'].astype(bool)
            us_true_indexes = pd.to_datetime(us_biz_data.index[~us_biz_data.values])

            # 将 datetime 类型转换为 Date 类型，并用 set() 函数转换为集合类型
            def date_to_Date(pydate):
                return str(Date(pydate.year, pydate.month, pydate.day))

            rlquantdata.DateUtilities.Calendar.sse_holDays = set([date_to_Date(d.date()) for d in true_indexes])
            rlquantdata.DateUtilities.Calendar.hkex_holDays = set([date_to_Date(d.date()) for d in hk_true_indexes])
            rlquantdata.DateUtilities.Calendar.nyse_holDays = set([date_to_Date(d.date()) for d in us_true_indexes])
        elif client is not None:
            """
            sorted_sse_holDays = sorted(list(rlquantdata.DateUtilities.Calendar.sse_holDays))
            result = client.get_remote_hol_dates(sorted_sse_holDays[-1])
            if result is None:
                print(f'无法从服务端获取交易日列表，使用预设交易日历。')
                result = []
            else:
                print(f'服务端获取交易日列表成功。')
            rlquantdata.DateUtilities.Calendar.sse_holDays.update(result)
            """
            for market in rlquantdata.DateUtilities.Calendar._holDict.keys():
                result = client.get_remote_hol_dates(market)
                if result is None:
                    print(f'无法从服务端获取{market}交易日列表，使用预设交易日历。')
                    result = []
                else:
                    print(f'服务端获取{market}交易日列表成功。')
                rlquantdata.DateUtilities.Calendar._holDict[market].updateHolDays(result)

        else:
            print(f'{trade_path} 路径无效，使用预设交易日历。')

    def isBizDay(self, holidayCenter, ref):
        return pai.isBizDay(holidayCenter, ref)

    def datesList(self, fromDate, toDate):
        return pai.datesList(fromDate, toDate)

    def bizDatesList(self, holidayCenter, fromDate, toDate):
        return pai.bizDatesList(holidayCenter, fromDate, toDate)

    def holDatesList(self, holidayCenter, fromDate, toDate, includeWeekend=True):
        return pai.holDatesList(holidayCenter, fromDate, toDate, includeWeekend)

    def advanceDate(self, referenceDate, period):
        return pai.advanceDate(referenceDate, period)

    def adjustDateByCalendar(self, holidayCenter, referenceDate, convention=BizDayConventions.Following):
        return pai.adjustDateByCalendar(holidayCenter, referenceDate, convention)

    def advanceDateByCalendar(self, holidayCenter, referenceDate, period, convention=BizDayConventions.Following):
        return pai.advanceDateByCalendar(holidayCenter, referenceDate, period, convention)

    def nthWeekDay(self, nth, dayOfWeek, month, year):
        return pai.nthWeekDay(nth, dayOfWeek, month, year)

    def makeSchedule(self, firstDate,
                     endDate,
                     tenor,
                     calendar='NullCalendar',
                     dateRule=BizDayConventions.Following,
                     dateGenerationRule=DateGeneration.Forward):
        return pai.makeSchedule(firstDate, endDate, tenor, calendar, dateRule, dateGenerationRule)
