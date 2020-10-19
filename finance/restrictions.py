# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from abc import ABC, abstractmethod
from functools import reduce
import pandas as pd, operator
from gateway.asset.assets import Asset
from _calendar.trading_calendar import calendar


class Restrictions(ABC):
    """
    Abstract restricted list interface, representing a set of asset that an
    algorithm is restricted from trading.
         --- used for pipe which filter asset list
    """

    @abstractmethod
    def is_restricted(self, assets, dt):
        """
        Is the asset restricted (RestrictionStates.FROZEN) on the given dt?

        Parameters
        ----------
        assets : Asset of iterable of Assets
            The asset(s) for which we are querying a restriction
        dt : pd.Timestamp
            The timestamp of the restriction query

        Returns
        -------
        is_restricted : bool or pd.Series[bool] indexed by asset
            Is the asset or asset restricted on this dt?

        """
        raise NotImplementedError('is_restricted')

    def __or__(self, other_restriction):
        """Base implementation for combining two restrictions.
        """
        # If the right side is a _UnionRestrictions, defers to the
        # _UnionRestrictions implementation of `|`, which intelligently
        # flattens restricted lists
        # 调用 _UnionRestrictions 的__or__
        if isinstance(other_restriction, UnionRestrictions):
            return other_restriction | self
        return UnionRestrictions([self, other_restriction])


class NoRestrictions(Restrictions):
    """
    A no-op restrictions that contains no restrictions.
    """
    def is_restricted(self, assets, dt):
        return assets


class StaticRestrictions(Restrictions):
    """
    Static restrictions stored in memory that are constant regardless of dt
    for each asset.

    Parameters
    ----------
    restricted_list : iterable of asset
        The asset to be restricted
    """

    def __init__(self, restricted_list):
        self._restricted_set = frozenset(restricted_list)

    def is_restricted(self, assets, dt):
        """
        An asset is restricted for all dts if it is in the static list.
        """
        selector = set(assets) - set(self._restricted_set)
        return selector


class SecurityListRestrictions(Restrictions):
    """
        a. 剔除停盘
        b. 剔除上市不足一个月的 --- 次新股波动性太大
        c. 剔除进入退市整理期的30个交易日
    """
    def __init__(self,
                 asset_finder,
                 window=[3*22, 30]):
        self.asset_finder = asset_finder
        self.window = window

    def is_restricted(self, assets, dt):
        s_date = calendar.dt_window_size(dt, self.window[0])
        e_date = calendar.dt_window_size(dt, self.window[-1])
        # alive assets --- means assets on dt can be traded
        active_assets = self.asset_finder.was_active(dt)
        # asset ipo date after s_date and asset delist date is before edate
        alive_assets = self.asset_finder.lifetime([s_date, e_date])
        ensure_assets = set(alive_assets) & set(active_assets)
        # intersection
        final_assets = set(assets) & set(ensure_assets)
        return final_assets


class AvailableRestrictions(Restrictions):
    """
        a. 受制于涨跌停限制
        b. 返回非限制的标的
    """
    def __init__(self,
                 data_portal,
                 threshold=0.0990):
        self.data_portal = data_portal
        self.threshold = threshold

    def is_restricted(self, assets, dts):
        open_pct, pre_close = self._data_portal.get_open_pct(assets, dts)
        final_assets = [asset for asset in assets if open_pct[asset] < self.threshold]
        return final_assets


class TemporaryRestrictions(object):
    """
        前5个交易日,科创板科创板还设置了临时停牌制度，当盘中股价较开盘价上涨或下跌幅度首次达到30%、60%时，都分别进行一次临时停牌
        单次盘中临时停牌的持续时间为10分钟。每个交易日单涨跌方向只能触发两次临时停牌，最多可以触发四次共计40分钟临时停牌。
        如果跨越14:57则复盘
    """
    def is_restricted(self, assets, dt):
        raise NotImplementedError()


class AfterRestrictions(object):
    """
        科创板盘后固定价格交易 15:00 --- 15:30
        若收盘价高于买入申报指令，则申报无效；若收盘价低于卖出申报指令同样无效
        原则 --- 以收盘价为成交价，按照时间优先的原则进行逐笔连续撮合
    """
    def is_restricted(self, assets, dt):
        raise NotImplementedError()


class UnionRestrictions(Restrictions):
    """
    A union of a number of sub restrictions.

    Parameters
    ----------
    sub_restrictions : iterable of Restrictions (but not _UnionRestrictions)
        The Restrictions to be added together

    Notes
    -----
    - Consumers should not construct instances of this class directly, but
      instead use the `|` operator to combine restrictions
    """

    def __new__(cls, sub_restrictions):
        # Filter out NoRestrictions and deal with resulting cases involving
        # one or zero sub_restrictions
        sub_restrictions = [
            r for r in sub_restrictions if not isinstance(r, NoRestrictions)
        ]
        if len(sub_restrictions) == 0:
            return NoRestrictions()
        elif len(sub_restrictions) == 1:
            return sub_restrictions[0]

        new_instance = super(UnionRestrictions, cls).__new__(cls)
        new_instance.sub_restrictions = sub_restrictions
        return new_instance

    def __or__(self, other_restriction):
        """
        Overrides the base implementation for combining two restrictions, of
        which the left side is a _UnionRestrictions.
        """
        # Flatten the underlying sub restrictions of _UnionRestrictions
        if isinstance(other_restriction, UnionRestrictions):
            new_sub_restrictions = \
                self.sub_restrictions + other_restriction.sub_restrictions
        else:
            new_sub_restrictions = self.sub_restrictions + [other_restriction]
        return UnionRestrictions(new_sub_restrictions)

    def is_restricted(self, assets, dt):
        if isinstance(assets, Asset):
            return assets if len(set(r.is_restricted(assets, dt)
                                     for r in self.sub_restrictions)) == 1 else None
        return reduce(
            operator.and_,
            (r.is_restricted(assets, dt) for r in self.sub_restrictions)
        )


__all__ = [
    'UnionRestrictions',
    'NoRestrictions',
    'StaticRestrictions',
    'SecurityListRestrictions',
    'AvailableRestrictions',
    'TemporaryRestrictions',
    'AfterRestrictions'
]


# if __name__ == '__main__':
#
#     from gateway.asset._finder import AssetFinder

#     finder = AssetFinder()
#     restriction = SecurityListRestrictions(finder)
#     print('restriction', restriction)
