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
import threading
from collections import deque
from bstack_utils.constants import *
class bstack11l11ll11_opy_:
    def __init__(self):
        self._1llllllllll1_opy_ = deque()
        self._11111111l11_opy_ = {}
        self._11111111lll_opy_ = False
        self._lock = threading.RLock()
    def bstack1111111l111_opy_(self, test_name, bstack11111111111_opy_):
        with self._lock:
            bstack1111111l1l1_opy_ = self._11111111l11_opy_.get(test_name, {})
            return bstack1111111l1l1_opy_.get(bstack11111111111_opy_, 0)
    def bstack1111111l11l_opy_(self, test_name, bstack11111111111_opy_):
        with self._lock:
            bstack111111111ll_opy_ = self.bstack1111111l111_opy_(test_name, bstack11111111111_opy_)
            self.bstack1lllllllllll_opy_(test_name, bstack11111111111_opy_)
            return bstack111111111ll_opy_
    def bstack1lllllllllll_opy_(self, test_name, bstack11111111111_opy_):
        with self._lock:
            if test_name not in self._11111111l11_opy_:
                self._11111111l11_opy_[test_name] = {}
            bstack1111111l1l1_opy_ = self._11111111l11_opy_[test_name]
            bstack111111111ll_opy_ = bstack1111111l1l1_opy_.get(bstack11111111111_opy_, 0)
            bstack1111111l1l1_opy_[bstack11111111111_opy_] = bstack111111111ll_opy_ + 1
    def bstack1ll1111l1_opy_(self, bstack11111111ll1_opy_, bstack111111111l1_opy_):
        bstack11111111l1l_opy_ = self.bstack1111111l11l_opy_(bstack11111111ll1_opy_, bstack111111111l1_opy_)
        event_name = bstack11l1ll11111_opy_[bstack111111111l1_opy_]
        bstack1l1l11l1lll_opy_ = bstack1111ll_opy_ (u"ࠣࡽࢀ࠱ࢀࢃ࠭ࡼࡿࠥᾈ").format(bstack11111111ll1_opy_, event_name, bstack11111111l1l_opy_)
        with self._lock:
            self._1llllllllll1_opy_.append(bstack1l1l11l1lll_opy_)
    def bstack1ll111lll_opy_(self):
        with self._lock:
            return len(self._1llllllllll1_opy_) == 0
    def bstack1lll11ll1l_opy_(self):
        with self._lock:
            if self._1llllllllll1_opy_:
                bstack1111111111l_opy_ = self._1llllllllll1_opy_.popleft()
                return bstack1111111111l_opy_
            return None
    def capturing(self):
        with self._lock:
            return self._11111111lll_opy_
    def bstack111111ll1_opy_(self):
        with self._lock:
            self._11111111lll_opy_ = True
    def bstack1ll1111ll1_opy_(self):
        with self._lock:
            self._11111111lll_opy_ = False