# coding: UTF-8
import sys
bstackl_opy_ = sys.version_info [0] == 2
bstack11l1_opy_ = 2048
bstack11ll_opy_ = 7
def bstack1111ll_opy_ (bstack1llllll1_opy_):
    global bstack1l111l1_opy_
    bstack11lllll_opy_ = ord (bstack1llllll1_opy_ [-1])
    bstack11llll_opy_ = bstack1llllll1_opy_ [:-1]
    bstack1ll1ll1_opy_ = bstack11lllll_opy_ % len (bstack11llll_opy_)
    bstack1ll1111_opy_ = bstack11llll_opy_ [:bstack1ll1ll1_opy_] + bstack11llll_opy_ [bstack1ll1ll1_opy_:]
    if bstackl_opy_:
        bstack111ll_opy_ = unicode () .join ([unichr (ord (char) - bstack11l1_opy_ - (bstack11l11_opy_ + bstack11lllll_opy_) % bstack11ll_opy_) for bstack11l11_opy_, char in enumerate (bstack1ll1111_opy_)])
    else:
        bstack111ll_opy_ = str () .join ([chr (ord (char) - bstack11l1_opy_ - (bstack11l11_opy_ + bstack11lllll_opy_) % bstack11ll_opy_) for bstack11l11_opy_, char in enumerate (bstack1ll1111_opy_)])
    return eval (bstack111ll_opy_)
import builtins
import logging
class bstack111l1lll1l_opy_:
    def __init__(self, handler):
        self._11l1llll11l_opy_ = builtins.print
        self.handler = handler
        self._started = False
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._11l1llll111_opy_ = {
            level: getattr(self.logger, level)
            for level in [bstack1111ll_opy_ (u"ࠫ࡮ࡴࡦࡰࠩឫ"), bstack1111ll_opy_ (u"ࠬࡪࡥࡣࡷࡪࠫឬ"), bstack1111ll_opy_ (u"࠭ࡷࡢࡴࡱ࡭ࡳ࡭ࠧឭ"), bstack1111ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ࠭ឮ")]
        }
    def start(self):
        if self._started:
            return
        self._started = True
        builtins.print = self._11l1lll1lll_opy_
        self._11l1llll1ll_opy_()
    def _11l1lll1lll_opy_(self, *args, **kwargs):
        self._11l1llll11l_opy_(*args, **kwargs)
        message = bstack1111ll_opy_ (u"ࠨࠢࠪឯ").join(map(str, args)) + bstack1111ll_opy_ (u"ࠩ࡟ࡲࠬឰ")
        self._log_message(bstack1111ll_opy_ (u"ࠪࡍࡓࡌࡏࠨឱ"), message)
    def _log_message(self, level, msg, *args, **kwargs):
        if self.handler:
            self.handler({bstack1111ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪឲ"): level, bstack1111ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭ឳ"): msg})
    def _11l1llll1ll_opy_(self):
        for level, bstack11l1lllll11_opy_ in self._11l1llll111_opy_.items():
            setattr(logging, level, self._11l1llll1l1_opy_(level, bstack11l1lllll11_opy_))
    def _11l1llll1l1_opy_(self, level, bstack11l1lllll11_opy_):
        def wrapper(msg, *args, **kwargs):
            bstack11l1lllll11_opy_(msg, *args, **kwargs)
            self._log_message(level.upper(), msg)
        return wrapper
    def reset(self):
        if not self._started:
            return
        self._started = False
        builtins.print = self._11l1llll11l_opy_
        for level, bstack11l1lllll11_opy_ in self._11l1llll111_opy_.items():
            setattr(logging, level, bstack11l1lllll11_opy_)