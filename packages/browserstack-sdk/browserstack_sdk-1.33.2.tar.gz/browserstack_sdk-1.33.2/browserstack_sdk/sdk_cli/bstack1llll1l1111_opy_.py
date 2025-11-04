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
import os
import threading
import os
from typing import Dict, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import timedelta
@dataclass
class bstack1llllll1111_opy_:
    id: str
    hash: str
    thread_id: int
    process_id: int
    type: str
class bstack1llll1l1lll_opy_:
    bstack11lll1l1l11_opy_ = bstack1111ll_opy_ (u"ࠢࡣࡧࡱࡧ࡭ࡳࡡࡳ࡭ࠥᘊ")
    context: bstack1llllll1111_opy_
    data: Dict[str, Any]
    platform_index: int
    def __init__(self, context: bstack1llllll1111_opy_):
        self.context = context
        self.data = dict({bstack1llll1l1lll_opy_.bstack11lll1l1l11_opy_: defaultdict(lambda: timedelta(microseconds=0))})
        self.platform_index = int(os.environ.get(bstack1111ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡌࡒࡉࡋࡘࠨᘋ"), bstack1111ll_opy_ (u"ࠩ࠳ࠫᘌ")))
    def ref(self) -> str:
        return str(self.context.id)
    def bstack1lllll111l1_opy_(self, target: object):
        return bstack1llll1l1lll_opy_.create_context(target) == self.context
    def bstack1l1llll111l_opy_(self, context: bstack1llllll1111_opy_):
        return context and context.thread_id == self.context.thread_id and context.process_id == self.context.process_id
    def bstack1ll1llll1_opy_(self, key: str, value: timedelta):
        self.data[bstack1llll1l1lll_opy_.bstack11lll1l1l11_opy_][key] += value
    def bstack1lll111lll1_opy_(self) -> dict:
        return self.data[bstack1llll1l1lll_opy_.bstack11lll1l1l11_opy_]
    @staticmethod
    def create_context(
        target: object,
        thread_id=threading.get_ident(),
        process_id=os.getpid(),
    ):
        return bstack1llllll1111_opy_(
            id=hash(target),
            hash=hash(target),
            thread_id=thread_id,
            process_id=process_id,
            type=target,
        )