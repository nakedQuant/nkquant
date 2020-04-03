# -*- coding : utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import os,datetime,pandas as pd,json,bcolz
from functools import partial
from decimal import Decimal
from GateWay.Spider.Tushare import TushareClient
from GateWay.Driver.Core import Core
from GateWay.Spider import Crawler
from Env.common import XML

class BarReader:

    def __init__(self):
        self.loader = Core()
        self.ts = TushareClient()
        self.extra = Crawler.ExtraOrdinary()

    def _verify_fields(self,f,asset):
        """如果asset为空，fields必须asset"""
        field = f.copy()
        if not isinstance(field,list):
            raise TypeError('fields must be list')
        elif asset is None:
            field.append('code')
        return field

    @staticmethod
    def calendar_foramtted(t):
        """将eg 20120907 --- 2012-09-07"""
        trans = ('-').join([t[:4],t[4:6],t[6:8]])
        return trans

    def load_trading_calendar(self, sdate, edate):
        """
            返回交易日列表 ， 类型为array
            session in range
        """
        calendar = self.loader.load_calendar(sdate, edate)
        trade_dt = list(map(self.calendar_foramtted,calendar))
        return trade_dt

    def is_market_caledar(self,dt):
        """判断是否交易日"""
        flag = self.loader.is_calendar(dt)
        return flag

    def load_calendar_offset(self, dt, window):
        """
            获取交易日偏移量
        """
        calendar_offset = self.loader.load_calendar_offset(dt, window)
        trade_dt = list(map(self.calendar_foramtted,calendar_offset))
        return trade_dt[-1]

    def load_stock_kline(self,sdate, edate,fields,asset):
        """
            返回特定时间区间日股票K线
        """
        fields = self._verify_fields(fields,asset)
        kline = self.loader.load_kline(sdate, edate, asset, 'asharePrice')
        kline = pd.DataFrame(kline,columns = ['trade_dt','code','open','close','high','low','volume'])
        kline.index = kline.loc[:,'trade_dt']
        kl_pd = kline.loc[:,fields]
        return kl_pd

    def load_kl_offset(self,asset,dt,window):
        """返回股票特定时间偏移的K线"""
        offset_kline = self.loader.load_ashare_kline_offset(dt,window,asset)
        offset_kl = pd.DataFrame(offset_kline,columns = ['trade_dt','open','close','high','low','volume'])
        return offset_kl

    def load_hk_kline(self, sdate, edate,fields, asset):
        """返回港股Kline"""
        fields = self._verify_fields(fields,asset)
        hk = self.loader.load_kline(sdate, edate, asset, 'hkPrice')
        hk_kline = pd.DataFrame(hk,columns = ['trade_dt','code','open','close','high','low','volume'])
        hk_kline.index = hk_kline.loc[:,'trade_dt']
        hk_pd = hk_kline.loc[:,fields]
        return hk_pd

    def load_etf_kline(self, sdate, edate,fields,asset):
        """
            返回特定时间区间日ETF k线
        """
        fields = self._verify_fields(fields,asset)
        etf = self.loader.load_kline(sdate, edate, asset, 'fundPrice')
        etf_kline = pd.DataFrame(etf,columns = ['trade_dt','code','open','close','high','low','volume'])
        etf_kline.index = etf_kline.loc[:,'trade_dt']
        etf_pd = etf_kline.loc[:,fields]
        return etf_pd

    def load_index_kline(self, sdate, edate,fields,asset):
        """
            返回特定时间区间日基准指数K线
        """
        fields = self._verify_fields(fields,asset)
        index = self.loader.load_kline(sdate, edate, asset, 'ashareIndex')
        index_kline = pd.DataFrame(index,columns = ['trade_dt','code','open','close','high','low','volume'])
        index_kline.index = index_kline.loc[:,'trade_dt']
        index_pd = index_kline.loc[:,fields]
        return index_pd

    def load_convertible_kline(self, sdate, edate,fields,asset):
        """
            返回特定时间区间日可转债K线
        """
        fields = self._verify_fields(fields,asset)
        convertible = self.loader.load_kline(sdate, edate, asset,'convertiblePrice')
        convertible_kline = pd.DataFrame(convertible,columns = ['trade_dt','code','open','close','high','low','volume'])
        convertible_kline.index = convertible_kline.loc[:,'trade_dt']
        convertible_pd = convertible_kline.loc[:,fields]
        return convertible_pd

    def load_ashare_basics(self, sid=None):
        basics = self.loader.load_stock_basics(sid)
        return basics

    def load_convertible_basics(self, bond):
        brief = self.loader.load_convertible_basics(bond)
        return brief

    def load_splits_divdend(self, sid):
         raw = self.loader.load_splits_divdend(sid)
         splitsDivdend = pd.DataFrame(raw,columns = ['除息日','送股','转增','派息'])
         splitsDivdend.sort_values(by='除息日',inplace = True)
         return splitsDivdend

    def _load_fq_coef(self, sid):
        """
           hfq --- 后复权 历史价格不变，现价变化
           qfq --- 前复权 现价不变 历史价格变化
        """
        raw = self.load_splits_divdend(sid)
        raw.index = raw['除息日']
        for i in raw.index:
            predate = self.load_calendar_offset(i,-1)
            data = self.load_kl_offset(sid,predate,1)
            if data.empty:
                data = self.load_kl_offset(sid,i,1)
            raw.loc[i,'preclose'] = data['close'].values[0]
        # #计算系数
        raw.loc[:,'coef'] = (Decimal.from_float(1) + (raw['送股']+raw['转增'])/Decimal.from_float(10)) / (Decimal.from_float(1) - raw['派息']/(raw['preclose'] * Decimal.from_float(10)))
        #上市日系数为1
        basics = self.loader.load_stock_basics(sid)
        timeTomarket = basics[0][1]
        raw.loc[timeTomarket,'coef'] = Decimal(1)
        raw.sort_index(inplace = True)
        coef = raw['coef'].cumprod()
        #将系数按照交易日进行填充
        trading_list = self.load_trading_calendar('1990-01-01','3000-01-01')
        coef = coef.reindex(trading_list)
        coef.fillna(method='ffill', inplace=True)
        coef.fillna(method='bfill', inplace=True)
        return coef

    def load_stock_hfq_kline(self,sdate,edate,fields,asset):
        """
            后复权kline ,如果基于前复权 --- 前视误差
        """
        coef = self._load_fq_coef(asset)
        kline = self.load_stock_kline(sdate,edate,fields,asset)
        kline.loc[:,'hfq'] = coef
        # #复权系数
        # kline.fillna(method = 'ffill',inplace = True)
        # kline.fillna(method = 'bfill',inplace = True)
        adjkline = pd.DataFrame()
        for f in fields:
            if f == 'volume':
                adjkline.loc[:,f] = kline.loc[:,f]
            adjkline.loc[:,f] = kline.loc[:, f] * kline.loc[:,'hfq']
        return adjkline

    def load_equity_info(self, sid):
        raw = self.loader.load_equity_structure(sid)
        structure = pd.DataFrame(raw,columns = ['code','change_dt','announce_dt','total_assets','float_assets','strict_assets','b_assets','h_assets'])
        return structure

    def load_market_value(self,sdate,edate,asset):
        """股票市场的市值情况"""
        raw = self.loader.load_ashare_mkv(sdate,edate,asset)
        market_value = pd.DataFrame(raw,columns = ['trade_dt','code','mkv','cap','strict','hk'])
        return market_value

    def load_minute_kline(self, sid, window):
        dt= datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
        if window:
            filename = ('-').join([dt,str(window), sid])
        else:
            filename = ('-').join([dt, sid])
        if filename not in os.listdir(XML.pathCsv.value):
            Crawler.Astock.download_ticks(sid, window)
        # 读取csv 数据
        minute_kline = self.load_prices_from_csv(filename)
        return minute_kline

    @staticmethod
    def load_prices_from_csv(filename):
        path = os.path.join(XML.pathCsv.value, filename)
        filepath = path + '.csv'
        try:
            _csv_dtypes = {
                'ticker': str,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int,
                'turnover': float,
                'avg': float,
            }
            read = partial(
                pd.read_csv,
                dtype=_csv_dtypes,index_col = 0,engine = 'python'
            )
            data = read(filepath)
            data.index = data.loc[:, 'ticker']
            data.sort_index(inplace=True)
        except:
            ValueError('csv file not exists')
        return data.iloc[:, 1:]

    def load_stock_holdings(self,sdate,edate,asset):
        """股东持仓变动"""
        raw = self.loader.load_ashare_holdings(sdate,edate,asset)
        holding = pd.DataFrame(raw,columns = ['变动截止日','代码','变动股本','占总流通比例','总持仓','占总股本比例','总流通股'])
        return holding

    def load_ashare_mass(self, sdate, edate):
        """
            获取时间区间内股票大宗交易，时间最好在一个月之内
        """
        mass = self.extra.download_mass(sdate, edate)
        return mass

    def load_ashare_release(self, sdate, edate):
        """
            获取A股解禁数据
        """
        release = self.extra.download_release(sdate, edate)
        return release

    def load_5d_minute_hk(self, h_code):
        """
            获取港股5日分钟线
            列名 -- ticker price volume
        """
        raw = self.extra.download_5d_minute_hk(h_code)
        return raw

    def load_stock_pledge(self,code):
        """股票质押率"""
        pledge = self.ts.to_ts_pledge(code)
        return pledge

    # def load_stock_suspend(self,dt,code=''):
    #     """股票的停盘状态,针对于交易日"""
    #     suspend = self.ts.to_ts_suspend(dt,code)
    #     return suspend

    def load_index_component(self,index,sdate,edate):
        """基准成分股以及对应权重 e.g. index_code='399300.SZ' """
        component = self.ts.to_ts_index_component(index,sdate,edate)
        return component

    def load_stock_status(self,code):
        """返回股票是否退市或者暂停上市"""
        raw = self.loader.load_stock_status(code)
        df = pd.DataFrame(raw,columns = ['code','status'])
        df = df if len(df) else None
        return df

    def load_ashare_hk_con(self, exchange, flag=1):
        """获取沪港通、深港通股票 , exchange 交易所 ; flag :1 最新的， 0 为历史的已经踢出的"""
        assets = self.ts.to_ts_con(exchange, flag)
        return assets

    def load_periphera_index(self, sdate, edate,fields,index, exchange):
        """us.DJI 道琼斯 us.IXIC 纳斯达克 us.INX  标普500 hkHSI 香港恒生指数 hkHSCEI 香港国企指数 hkHSCCI 香港红筹指数"""
        raw = self.extra.download_periphera_index(sdate, edate,index, exchange)
        raw.index = raw['trade_dt']
        index_price = raw.loc[:,fields]
        return index_price

    def load_market_margin(self,sdate,edate):
        """整个A股市场融资融券余额"""
        margin = self.loader.load_market_margin(sdate,edate)
        market_margin = pd.DataFrame(margin,columns = ['交易日期','融资余额','融券余额','融资融券总额','融资融券差额'])
        return market_margin

    def load_gdp(self):
        gdp = self.extra.download_gross_value()
        gdp['总值'] = gdp['总值'].astype('float64')
        return gdp

class BarWriter:

    def __init__(self, path):

        self.sid_path = path

    def _write_csv(self, data):
        """
            dump to csv
        """
        if isinstance(data, pd.DataFrame):
            data.to_csv(self.sid_path)
        else:
            with open(self.sid_path, mode='w') as file:
                if isinstance(data, str):
                    file.write(data)
                else:
                    for chunk in data:
                        file.write(chunk)

    def _init_hdf5(self, frames, _complevel=5, _complib='zlib'):
        if isinstance(frames, json):
            frames = json.dumps(frames)
        with pd.HDFStore(self.sid_path, 'w', complevel=_complevel, complib=_complib) as store:
            panel = pd.Panel.from_dict(frames)
            panel.to_hdf(store)
            panel = pd.read_hdf(self.sid_path)
        return panel

    def _init_ctable(self, raw):
        """
            Obtain 、Create 、Append、Attr empty ctable for given path.
            addcol(newcol[, name, pos, move])	Add a new newcol object as column.
            append(cols)	Append cols to this ctable -- e.g. : ctable
            Flush data in internal buffers to disk:
                This call should typically be done after performing modifications
                (__settitem__(), append()) in persistence mode. If you don’t do this,
                you risk losing part of your modifications.

        """
        ctable = bcolz.ctable(rootdir=self.sid_path, columns=None, names= \
            ['open', 'high', 'low', 'close', 'volume'], mode='w')

        if isinstance(raw, pd.DataFrame):
            ctable.fromdataframe(raw)
        elif isinstance(raw, dict):
            for k, v in raw.items():
                ctable.attrs[k] = v
        elif isinstance(raw, list):
            ctable.append([raw])
        #
        ctable.flush()

    @staticmethod
    def load_prices_from_ctable(file):
        """
            bcolz.open return a carray/ctable object or IOError (if not objects are found)
            ‘r’ for read-only
            ‘w’ for emptying the previous underlying data
            ‘a’ for allowing read/write on top of existing data
        """
        sid_path = os.path.join(XML.CTABLE, file)
        table = bcolz.open(rootdir=sid_path, mode='r')
        df = table.todataframe(columns=[
            'open',
            'high',
            'low',
            'close',
            'volume'
        ])
        return df


if __name__ == '__main__':

    bar = BarReader()

    fields = ['close']

    flag = bar.is_market_caledar('2020-02-17')
    print('flag',flag)

    calendar = bar.load_trading_calendar('2015-01-01','2015-04-01')
    print('calendar',calendar)
    #
    offset = bar.load_calendar_offset('2010-01-01', 1)
    print('offset',offset)
    #
    # hfq_kline = bar.load_stock_hfq_kline('2020-01-01','2020-02-20',fields,'000001')
    # print('hfq_kline',hfq_kline)
    #
    # kline = bar.load_stock_kline('2014-01-01', '2014-04-01',fields,'000001')
    # print('stock kline',kline)
    #
    # hk_kline = bar.load_hk_kline('2012-01-02', '2012-03-01',fields,'000001')
    # print('hk kline',hk_kline)
    #
    # etf_kline = bar.load_etf_kline('2015-02-02','2015-04-01',fields)
    # print('etf kline',etf_kline)
    #
    # index_kline = bar.load_index_kline('2014-01-02','2014-04-01',fields,'000001')
    # print('index kline',index_kline)
    #
    # convertible_kline = bar.load_convertible_kline('2015-02-02','2015-04-01',fields)
    # print('convertible_kline',convertible_kline)
    #
    # offset_kline = bar.load_kl_offset('000001','2007-06-17',1)
    # print('offset_kline',offset_kline)
    #
    # basics = bar.load_ashare_basics('002570')
    # print('stock basics',basics)
    #
    # basics_ = bar.load_convertible_basics('123021')
    # print('convetible basics',basics_)
    #
    # splits = bar.load_splits_divdend('002570')
    # print('stock splits and divdend',splits)
    #
    # equity = bar.load_equity_info('002570')
    # print('equity',equity)

    # market_value = bar.load_market_value('2019-01-01','2020-01-20')
    # print('mkv',market_value)

    # holding = bar.load_stock_holdings('2020-01-01','2020-02-30',None)
    # print('holding',holding)
    #
    # minute_kline = bar.load_minute_kline('002570',5)
    # print('minute kline',minute_kline)
    #
    # status = bar.load_stock_status()
    # print('status',status)

    # mass = bar.load_ashare_mass('2020-01-01','2020-02-13')
    # print('stock mass transaction',mass)

    # release = bar.load_ashare_release('2020-01-01','2020-03-01')
    # print('release',release)

    # pledge = bar.load_stock_pledge('002570')
    # print('pledge',pledge)

    # # 权限不够
    # component = bar.load_index_component('399300.SZ','20190101','20200220')
    # print('index_component',component)

    # minute_5d = bar.load_5d_minute_hk('01033')
    # print('h_code_5d_minute_kline',minute_5d)
    #
    # suspend_status = bar.load_stock_suspend('','002570')
    # print('stock_code ssupend record',suspend_status)
    # #
    # con = bar.load_ashare_hk_con('SH',0)
    # print('沪股通或者深港通标的',con)
    #
    # foreign_index = bar.load_periphera_index('2020-01-01','2020-03-01',['close'],'DJI','us')
    # print('foreign index',foreign_index)
    # #
    # margin = bar.load_market_margin('2020-02-11','2020-02-30')
    # print('margin',margin)
