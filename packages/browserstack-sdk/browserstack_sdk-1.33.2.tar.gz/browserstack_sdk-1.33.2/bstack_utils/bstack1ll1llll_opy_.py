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
from time import sleep
from datetime import datetime
from urllib.parse import urlencode
from bstack_utils.bstack11l1lllll1l_opy_ import bstack11l1lllllll_opy_
from bstack_utils.constants import *
import json
class bstack1ll111l1l1_opy_:
    def __init__(self, bstack1lll11l111_opy_, bstack11ll111111l_opy_):
        self.bstack1lll11l111_opy_ = bstack1lll11l111_opy_
        self.bstack11ll111111l_opy_ = bstack11ll111111l_opy_
        self.bstack11ll1111l11_opy_ = None
    def __call__(self):
        bstack11ll11111ll_opy_ = {}
        while True:
            self.bstack11ll1111l11_opy_ = bstack11ll11111ll_opy_.get(
                bstack1111ll_opy_ (u"࠭࡮ࡦࡺࡷࡣࡵࡵ࡬࡭ࡡࡷ࡭ࡲ࡫ࠧម"),
                int(datetime.now().timestamp() * 1000)
            )
            bstack11l1llllll1_opy_ = self.bstack11ll1111l11_opy_ - int(datetime.now().timestamp() * 1000)
            if bstack11l1llllll1_opy_ > 0:
                sleep(bstack11l1llllll1_opy_ / 1000)
            params = {
                bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧយ"): self.bstack1lll11l111_opy_,
                bstack1111ll_opy_ (u"ࠨࡶ࡬ࡱࡪࡹࡴࡢ࡯ࡳࠫរ"): int(datetime.now().timestamp() * 1000)
            }
            bstack11ll11111l1_opy_ = bstack1111ll_opy_ (u"ࠤ࡫ࡸࡹࡶࡳ࠻࠱࠲ࠦល") + bstack11ll1111l1l_opy_ + bstack1111ll_opy_ (u"ࠥ࠳ࡦࡻࡴࡰ࡯ࡤࡸࡪ࠵ࡡࡱ࡫࠲ࡺ࠶࠵ࠢវ")
            if self.bstack11ll111111l_opy_.lower() == bstack1111ll_opy_ (u"ࠦࡷ࡫ࡳࡶ࡮ࡷࡷࠧឝ"):
                bstack11ll11111ll_opy_ = bstack11l1lllllll_opy_.results(bstack11ll11111l1_opy_, params)
            else:
                bstack11ll11111ll_opy_ = bstack11l1lllllll_opy_.bstack11ll1111111_opy_(bstack11ll11111l1_opy_, params)
            if str(bstack11ll11111ll_opy_.get(bstack1111ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬឞ"), bstack1111ll_opy_ (u"࠭࠲࠱࠲ࠪស"))) != bstack1111ll_opy_ (u"ࠧ࠵࠲࠷ࠫហ"):
                break
        return bstack11ll11111ll_opy_.get(bstack1111ll_opy_ (u"ࠨࡦࡤࡸࡦ࠭ឡ"), bstack11ll11111ll_opy_)