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
from typing import Dict, List, Any, Callable, Tuple, Union
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.bstack1ll1ll1llll_opy_ import bstack1ll1lll111l_opy_
from browserstack_sdk.sdk_cli.bstack1llllll1l1l_opy_ import (
    bstack1llll11llll_opy_,
    bstack1lllll1lll1_opy_,
    bstack1lllll1111l_opy_,
)
from bstack_utils.helper import  bstack1l1l11ll1l_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lllll1_opy_ import bstack1lll11lllll_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1l11lll1_opy_, bstack1lll1llllll_opy_, bstack1lll1l111ll_opy_, bstack1ll1l1l1111_opy_
from typing import Tuple, Any
import threading
from bstack_utils.bstack11lll11l11_opy_ import bstack11l11ll11_opy_
from browserstack_sdk.sdk_cli.bstack1lll1ll1l1l_opy_ import bstack1lll1111lll_opy_
from bstack_utils.percy import bstack1lll1l1l_opy_
from bstack_utils.percy_sdk import PercySDK
from bstack_utils.constants import *
import re
class bstack1ll1l1lll1l_opy_(bstack1ll1lll111l_opy_):
    def __init__(self, bstack1l1l11lll11_opy_: Dict[str, str]):
        super().__init__()
        self.bstack1l1l11lll11_opy_ = bstack1l1l11lll11_opy_
        self.percy = bstack1lll1l1l_opy_()
        self.bstack11l1l1ll11_opy_ = bstack11l11ll11_opy_()
        self.bstack1l1l11ll1ll_opy_()
        bstack1lll11lllll_opy_.bstack1ll111ll1l1_opy_((bstack1llll11llll_opy_.bstack1lllll11ll1_opy_, bstack1lllll1lll1_opy_.PRE), self.bstack1l1l11ll111_opy_)
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.POST), self.bstack1ll11l1ll11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l1ll111lll_opy_(self, instance: bstack1lllll1111l_opy_, driver: object):
        bstack1l1l1l111ll_opy_ = TestFramework.bstack1llll11lll1_opy_(instance.context)
        for t in bstack1l1l1l111ll_opy_:
            bstack1l1lll11111_opy_ = TestFramework.bstack1llllll1lll_opy_(t, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
            if any(instance is d[1] for d in bstack1l1lll11111_opy_) or instance == driver:
                return t
    def bstack1l1l11ll111_opy_(
        self,
        f: bstack1lll11lllll_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        try:
            instance, method_name = exec
            if not bstack1lll11lllll_opy_.bstack1ll11ll11ll_opy_(method_name):
                return
            platform_index = f.bstack1llllll1lll_opy_(instance, bstack1lll11lllll_opy_.bstack1ll11ll1l11_opy_, 0)
            bstack1l1l11lllll_opy_ = self.bstack1l1ll111lll_opy_(instance, driver)
            bstack1l1l11l1lll_opy_ = TestFramework.bstack1llllll1lll_opy_(bstack1l1l11lllll_opy_, TestFramework.bstack1l1l11l1l11_opy_, None)
            if not bstack1l1l11l1lll_opy_:
                self.logger.debug(bstack1111ll_opy_ (u"ࠣࡱࡱࡣࡵࡸࡥࡠࡧࡻࡩࡨࡻࡴࡦ࠼ࠣࡶࡪࡺࡵࡳࡰ࡬ࡲ࡬ࠦࡡࡴࠢࡶࡩࡸࡹࡩࡰࡰࠣ࡭ࡸࠦ࡮ࡰࡶࠣࡽࡪࡺࠠࡴࡶࡤࡶࡹ࡫ࡤࠣጂ"))
                return
            driver_command = f.bstack1ll1111llll_opy_(*args)
            for command in bstack1111ll11_opy_:
                if command == driver_command:
                    self.bstack1ll11111l1_opy_(driver, platform_index)
            bstack1lll111ll_opy_ = self.percy.bstack1l1lll11_opy_()
            if driver_command in bstack1l11ll111_opy_[bstack1lll111ll_opy_]:
                self.bstack11l1l1ll11_opy_.bstack1ll1111l1_opy_(bstack1l1l11l1lll_opy_, driver_command)
        except Exception as e:
            self.logger.error(bstack1111ll_opy_ (u"ࠤࡲࡲࡤࡶࡲࡦࡡࡨࡼࡪࡩࡵࡵࡧ࠽ࠤࡪࡸࡲࡰࡴࠥጃ"), e)
    def bstack1ll11l1ll11_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        from bstack_utils.bstack11lll111l_opy_ import bstack1ll1lllll1l_opy_
        bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠥࡳࡳࡥࡡࡧࡶࡨࡶࡤࡺࡥࡴࡶ࠽ࠤࡳࡵࠠࡥࡴ࡬ࡺࡪࡸࡳࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧጄ") + str(kwargs) + bstack1111ll_opy_ (u"ࠦࠧጅ"))
            return
        if len(bstack1l1lll11111_opy_) > 1:
            self.logger.debug(bstack1111ll_opy_ (u"ࠧࡵ࡮ࡠࡣࡩࡸࡪࡸ࡟ࡵࡧࡶࡸ࠿ࠦࡻ࡭ࡧࡱࠬࡩࡸࡩࡷࡧࡵࡣ࡮ࡴࡳࡵࡣࡱࡧࡪࡹࠩࡾࠢࡧࡶ࡮ࡼࡥࡳࡵࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢጆ") + str(kwargs) + bstack1111ll_opy_ (u"ࠨࠢጇ"))
        bstack1l1l11l1111_opy_, bstack1l1l11l1ll1_opy_ = bstack1l1lll11111_opy_[0]
        driver = bstack1l1l11l1111_opy_()
        if not driver:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡰࡰࡢࡥ࡫ࡺࡥࡳࡡࡷࡩࡸࡺ࠺ࠡࡰࡲࠤࡩࡸࡩࡷࡧࡵࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣገ") + str(kwargs) + bstack1111ll_opy_ (u"ࠣࠤጉ"))
            return
        bstack1l1l11l1l1l_opy_ = {
            TestFramework.bstack1ll11111l1l_opy_: bstack1111ll_opy_ (u"ࠤࡷࡩࡸࡺࠠ࡯ࡣࡰࡩࠧጊ"),
            TestFramework.bstack1ll111l1lll_opy_: bstack1111ll_opy_ (u"ࠥࡸࡪࡹࡴࠡࡷࡸ࡭ࡩࠨጋ"),
            TestFramework.bstack1l1l11l1l11_opy_: bstack1111ll_opy_ (u"ࠦࡹ࡫ࡳࡵࠢࡵࡩࡷࡻ࡮ࠡࡰࡤࡱࡪࠨጌ")
        }
        bstack1l1l11ll11l_opy_ = { key: f.bstack1llllll1lll_opy_(instance, key) for key in bstack1l1l11l1l1l_opy_ }
        bstack1l1l11l11l1_opy_ = [key for key, value in bstack1l1l11ll11l_opy_.items() if not value]
        if bstack1l1l11l11l1_opy_:
            for key in bstack1l1l11l11l1_opy_:
                self.logger.debug(bstack1111ll_opy_ (u"ࠧࡵ࡮ࡠࡣࡩࡸࡪࡸ࡟ࡵࡧࡶࡸ࠿ࠦ࡭ࡪࡵࡶ࡭ࡳ࡭ࠠࠣግ") + str(key) + bstack1111ll_opy_ (u"ࠨࠢጎ"))
            return
        platform_index = f.bstack1llllll1lll_opy_(instance, bstack1lll11lllll_opy_.bstack1ll11ll1l11_opy_, 0)
        if self.bstack1l1l11lll11_opy_.percy_capture_mode == bstack1111ll_opy_ (u"ࠢࡵࡧࡶࡸࡨࡧࡳࡦࠤጏ"):
            bstack1ll1lllll_opy_ = bstack1l1l11ll11l_opy_.get(TestFramework.bstack1l1l11l1l11_opy_) + bstack1111ll_opy_ (u"ࠣ࠯ࡷࡩࡸࡺࡣࡢࡵࡨࠦጐ")
            bstack1ll1111l1l1_opy_ = bstack1ll1lllll1l_opy_.bstack1ll11ll111l_opy_(EVENTS.bstack1l1l11ll1l1_opy_.value)
            PercySDK.screenshot(
                driver,
                bstack1ll1lllll_opy_,
                bstack111ll111_opy_=bstack1l1l11ll11l_opy_[TestFramework.bstack1ll11111l1l_opy_],
                bstack1ll1l1ll11_opy_=bstack1l1l11ll11l_opy_[TestFramework.bstack1ll111l1lll_opy_],
                bstack1l1l1lll_opy_=platform_index
            )
            bstack1ll1lllll1l_opy_.end(EVENTS.bstack1l1l11ll1l1_opy_.value, bstack1ll1111l1l1_opy_+bstack1111ll_opy_ (u"ࠤ࠽ࡷࡹࡧࡲࡵࠤ጑"), bstack1ll1111l1l1_opy_+bstack1111ll_opy_ (u"ࠥ࠾ࡪࡴࡤࠣጒ"), True, None, None, None, None, test_name=bstack1ll1lllll_opy_)
    def bstack1ll11111l1_opy_(self, driver, platform_index):
        if self.bstack11l1l1ll11_opy_.bstack1ll111lll_opy_() is True or self.bstack11l1l1ll11_opy_.capturing() is True:
            return
        self.bstack11l1l1ll11_opy_.bstack111111ll1_opy_()
        while not self.bstack11l1l1ll11_opy_.bstack1ll111lll_opy_():
            bstack1l1l11l1lll_opy_ = self.bstack11l1l1ll11_opy_.bstack1lll11ll1l_opy_()
            self.bstack1l11lll1_opy_(driver, bstack1l1l11l1lll_opy_, platform_index)
        self.bstack11l1l1ll11_opy_.bstack1ll1111ll1_opy_()
    def bstack1l11lll1_opy_(self, driver, bstack1l11111l1l_opy_, platform_index, test=None):
        from bstack_utils.bstack11lll111l_opy_ import bstack1ll1lllll1l_opy_
        bstack1ll1111l1l1_opy_ = bstack1ll1lllll1l_opy_.bstack1ll11ll111l_opy_(EVENTS.bstack11llll1lll_opy_.value)
        if test != None:
            bstack111ll111_opy_ = getattr(test, bstack1111ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩጓ"), None)
            bstack1ll1l1ll11_opy_ = getattr(test, bstack1111ll_opy_ (u"ࠬࡻࡵࡪࡦࠪጔ"), None)
            PercySDK.screenshot(driver, bstack1l11111l1l_opy_, bstack111ll111_opy_=bstack111ll111_opy_, bstack1ll1l1ll11_opy_=bstack1ll1l1ll11_opy_, bstack1l1l1lll_opy_=platform_index)
        else:
            PercySDK.screenshot(driver, bstack1l11111l1l_opy_)
        bstack1ll1lllll1l_opy_.end(EVENTS.bstack11llll1lll_opy_.value, bstack1ll1111l1l1_opy_+bstack1111ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨጕ"), bstack1ll1111l1l1_opy_+bstack1111ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧ጖"), True, None, None, None, None, test_name=bstack1l11111l1l_opy_)
    def bstack1l1l11ll1ll_opy_(self):
        os.environ[bstack1111ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡇࡕࡇ࡞࠭጗")] = str(self.bstack1l1l11lll11_opy_.success)
        os.environ[bstack1111ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡒࡈࡖࡈ࡟࡟ࡄࡃࡓࡘ࡚ࡘࡅࡠࡏࡒࡈࡊ࠭ጘ")] = str(self.bstack1l1l11lll11_opy_.percy_capture_mode)
        self.percy.bstack1l1l11l11ll_opy_(self.bstack1l1l11lll11_opy_.is_percy_auto_enabled)
        self.percy.bstack1l1l11l111l_opy_(self.bstack1l1l11lll11_opy_.percy_build_id)