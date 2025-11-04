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
from bstack_utils.constants import bstack11ll1111lll_opy_
def bstack11l1111ll_opy_(bstack11ll1111ll1_opy_):
    from browserstack_sdk.sdk_cli.cli import cli
    from bstack_utils.helper import bstack1ll1l11lll_opy_
    host = bstack1ll1l11lll_opy_(cli.config, [bstack1111ll_opy_ (u"ࠤࡤࡴ࡮ࡹࠢប"), bstack1111ll_opy_ (u"ࠥࡥࡺࡺ࡯࡮ࡣࡷࡩࠧផ"), bstack1111ll_opy_ (u"ࠦࡦࡶࡩࠣព")], bstack11ll1111lll_opy_)
    return bstack1111ll_opy_ (u"ࠬࢁࡽ࠰ࡽࢀࠫភ").format(host, bstack11ll1111ll1_opy_)