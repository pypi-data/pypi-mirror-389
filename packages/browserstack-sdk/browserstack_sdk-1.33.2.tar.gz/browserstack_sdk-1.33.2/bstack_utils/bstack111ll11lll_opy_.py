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
from bstack_utils.helper import bstack11l11ll1ll_opy_
from bstack_utils.constants import bstack11l1l1ll1l1_opy_, EVENTS, STAGE
from bstack_utils.bstack1lll1llll1_opy_ import get_logger
logger = get_logger(__name__)
class bstack1ll1l111l1_opy_:
    bstack1lllll1ll1l1_opy_ = None
    @classmethod
    def bstack1l111l1ll1_opy_(cls):
        if cls.on() and os.getenv(bstack1111ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢ࡙࡚ࡏࡄࠣ≍")):
            logger.info(
                bstack1111ll_opy_ (u"࡛ࠫ࡯ࡳࡪࡶࠣ࡬ࡹࡺࡰࡴ࠼࠲࠳ࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰ࠳ࡧࡻࡩ࡭ࡦࡶ࠳ࢀࢃࠠࡵࡱࠣࡺ࡮࡫ࡷࠡࡤࡸ࡭ࡱࡪࠠࡳࡧࡳࡳࡷࡺࠬࠡ࡫ࡱࡷ࡮࡭ࡨࡵࡵ࠯ࠤࡦࡴࡤࠡ࡯ࡤࡲࡾࠦ࡭ࡰࡴࡨࠤࡩ࡫ࡢࡶࡩࡪ࡭ࡳ࡭ࠠࡪࡰࡩࡳࡷࡳࡡࡵ࡫ࡲࡲࠥࡧ࡬࡭ࠢࡤࡸࠥࡵ࡮ࡦࠢࡳࡰࡦࡩࡥࠢ࡞ࡱࠫ≎").format(os.getenv(bstack1111ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠥ≏"))))
    @classmethod
    def on(cls):
        if os.environ.get(bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡊࡘࡖࠪ≐"), None) is None or os.environ[bstack1111ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ≑")] == bstack1111ll_opy_ (u"ࠣࡰࡸࡰࡱࠨ≒"):
            return False
        return True
    @classmethod
    def bstack1lll1llllll1_opy_(cls, bs_config, framework=bstack1111ll_opy_ (u"ࠤࠥ≓")):
        bstack11l1lll1l1l_opy_ = False
        for fw in bstack11l1l1ll1l1_opy_:
            if fw in framework:
                bstack11l1lll1l1l_opy_ = True
        return bstack11l11ll1ll_opy_(bs_config.get(bstack1111ll_opy_ (u"ࠪࡸࡪࡹࡴࡐࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࠧ≔"), bstack11l1lll1l1l_opy_))
    @classmethod
    def bstack1lll1lll1ll1_opy_(cls, framework):
        return framework in bstack11l1l1ll1l1_opy_
    @classmethod
    def bstack1llll11l111l_opy_(cls, bs_config, framework):
        return cls.bstack1lll1llllll1_opy_(bs_config, framework) is True and cls.bstack1lll1lll1ll1_opy_(framework)
    @staticmethod
    def current_hook_uuid():
        return getattr(threading.current_thread(), bstack1111ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤ࡮࡯ࡰ࡭ࡢࡹࡺ࡯ࡤࠨ≕"), None)
    @staticmethod
    def bstack111l1ll11l_opy_():
        if getattr(threading.current_thread(), bstack1111ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣࡺࡻࡩࡥࠩ≖"), None):
            return {
                bstack1111ll_opy_ (u"࠭ࡴࡺࡲࡨࠫ≗"): bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࠬ≘"),
                bstack1111ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ≙"): getattr(threading.current_thread(), bstack1111ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢࡸࡪࡹࡴࡠࡷࡸ࡭ࡩ࠭≚"), None)
            }
        if getattr(threading.current_thread(), bstack1111ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣ࡭ࡵ࡯࡬ࡡࡸࡹ࡮ࡪࠧ≛"), None):
            return {
                bstack1111ll_opy_ (u"ࠫࡹࡿࡰࡦࠩ≜"): bstack1111ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࠪ≝"),
                bstack1111ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭≞"): getattr(threading.current_thread(), bstack1111ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡪࡲࡳࡰࡥࡵࡶ࡫ࡧࠫ≟"), None)
            }
        return None
    @staticmethod
    def bstack1lll1lll1l11_opy_(func):
        def wrap(*args, **kwargs):
            if bstack1ll1l111l1_opy_.on():
                return func(*args, **kwargs)
            return
        return wrap
    @staticmethod
    def bstack111l111l11_opy_(test, hook_name=None):
        bstack1lll1lll1l1l_opy_ = test.parent
        if hook_name in [bstack1111ll_opy_ (u"ࠨࡵࡨࡸࡺࡶ࡟ࡤ࡮ࡤࡷࡸ࠭≠"), bstack1111ll_opy_ (u"ࠩࡷࡩࡦࡸࡤࡰࡹࡱࡣࡨࡲࡡࡴࡵࠪ≡"), bstack1111ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࡡࡰࡳࡩࡻ࡬ࡦࠩ≢"), bstack1111ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳࡥ࡭ࡰࡦࡸࡰࡪ࠭≣")]:
            bstack1lll1lll1l1l_opy_ = test
        scope = []
        while bstack1lll1lll1l1l_opy_ is not None:
            scope.append(bstack1lll1lll1l1l_opy_.name)
            bstack1lll1lll1l1l_opy_ = bstack1lll1lll1l1l_opy_.parent
        scope.reverse()
        return scope[2:]
    @staticmethod
    def bstack1lll1lll11ll_opy_(hook_type):
        if hook_type == bstack1111ll_opy_ (u"ࠧࡈࡅࡇࡑࡕࡉࡤࡋࡁࡄࡊࠥ≤"):
            return bstack1111ll_opy_ (u"ࠨࡓࡦࡶࡸࡴࠥ࡮࡯ࡰ࡭ࠥ≥")
        elif hook_type == bstack1111ll_opy_ (u"ࠢࡂࡈࡗࡉࡗࡥࡅࡂࡅࡋࠦ≦"):
            return bstack1111ll_opy_ (u"ࠣࡖࡨࡥࡷࡪ࡯ࡸࡰࠣ࡬ࡴࡵ࡫ࠣ≧")
    @staticmethod
    def bstack1lll1lll1lll_opy_(bstack1lll1ll11_opy_):
        try:
            if not bstack1ll1l111l1_opy_.on():
                return bstack1lll1ll11_opy_
            if os.environ.get(bstack1111ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡔࡈࡖ࡚ࡔࠢ≨"), None) == bstack1111ll_opy_ (u"ࠥࡸࡷࡻࡥࠣ≩"):
                tests = os.environ.get(bstack1111ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡖࡊࡘࡕࡏࡡࡗࡉࡘ࡚ࡓࠣ≪"), None)
                if tests is None or tests == bstack1111ll_opy_ (u"ࠧࡴࡵ࡭࡮ࠥ≫"):
                    return bstack1lll1ll11_opy_
                bstack1lll1ll11_opy_ = tests.split(bstack1111ll_opy_ (u"࠭ࠬࠨ≬"))
                return bstack1lll1ll11_opy_
        except Exception as exc:
            logger.debug(bstack1111ll_opy_ (u"ࠢࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡲࡦࡴࡸࡲࠥ࡮ࡡ࡯ࡦ࡯ࡩࡷࡀࠠࠣ≭") + str(str(exc)) + bstack1111ll_opy_ (u"ࠣࠤ≮"))
        return bstack1lll1ll11_opy_