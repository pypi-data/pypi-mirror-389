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
import logging
import bstack_utils.accessibility as bstack1l1111lll_opy_
from bstack_utils.helper import bstack1l1l11ll1l_opy_
logger = logging.getLogger(__name__)
def bstack1lll1l111_opy_(bstack1l1ll11111_opy_):
  return True if bstack1l1ll11111_opy_ in threading.current_thread().__dict__.keys() else False
def bstack1l11lll11_opy_(context, *args):
    tags = getattr(args[0], bstack1111ll_opy_ (u"ࠩࡷࡥ࡬ࡹࠧអ"), [])
    bstack1111111ll_opy_ = bstack1l1111lll_opy_.bstack1l1l1l11l1_opy_(tags)
    threading.current_thread().isA11yTest = bstack1111111ll_opy_
    try:
      bstack1ll1l11ll_opy_ = threading.current_thread().bstackSessionDriver if bstack1lll1l111_opy_(bstack1111ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭ࡖࡩࡸࡹࡩࡰࡰࡇࡶ࡮ࡼࡥࡳࠩឣ")) else context.browser
      if bstack1ll1l11ll_opy_ and bstack1ll1l11ll_opy_.session_id and bstack1111111ll_opy_ and bstack1l1l11ll1l_opy_(
              threading.current_thread(), bstack1111ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪឤ"), None):
          threading.current_thread().isA11yTest = bstack1l1111lll_opy_.bstack1lllll1l1l_opy_(bstack1ll1l11ll_opy_, bstack1111111ll_opy_)
    except Exception as e:
       logger.debug(bstack1111ll_opy_ (u"ࠬࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡵࡷࡥࡷࡺࠠࡢ࠳࠴ࡽࠥ࡯࡮ࠡࡤࡨ࡬ࡦࡼࡥ࠻ࠢࡾࢁࠬឥ").format(str(e)))
def bstack11l111111l_opy_(bstack1ll1l11ll_opy_):
    if bstack1l1l11ll1l_opy_(threading.current_thread(), bstack1111ll_opy_ (u"࠭ࡩࡴࡃ࠴࠵ࡾ࡚ࡥࡴࡶࠪឦ"), None) and bstack1l1l11ll1l_opy_(
      threading.current_thread(), bstack1111ll_opy_ (u"ࠧࡢ࠳࠴ࡽࡕࡲࡡࡵࡨࡲࡶࡲ࠭ឧ"), None) and not bstack1l1l11ll1l_opy_(threading.current_thread(), bstack1111ll_opy_ (u"ࠨࡣ࠴࠵ࡾࡥࡳࡵࡱࡳࠫឨ"), False):
      threading.current_thread().a11y_stop = True
      bstack1l1111lll_opy_.bstack1l1ll111_opy_(bstack1ll1l11ll_opy_, name=bstack1111ll_opy_ (u"ࠤࠥឩ"), path=bstack1111ll_opy_ (u"ࠥࠦឪ"))