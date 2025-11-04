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
import json
import time
import os
import threading
import asyncio
from browserstack_sdk.sdk_cli.bstack1llllll1l1l_opy_ import (
    bstack1llll11llll_opy_,
    bstack1lllll1lll1_opy_,
    bstack1lllll1111l_opy_,
    bstack1llllll1111_opy_,
)
from typing import Tuple, Dict, Any, List, Union
from bstack_utils.helper import bstack1l1l1llll11_opy_, bstack1l1l11lll1_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lllll1_opy_ import bstack1lll11lllll_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_, bstack1lll1llllll_opy_
from browserstack_sdk.sdk_cli.bstack1lll1ll1lll_opy_ import bstack1lll11ll111_opy_
from browserstack_sdk.sdk_cli.bstack1l1lll1l1ll_opy_ import bstack1l1lll11l1l_opy_
from typing import Tuple, List, Any
from bstack_utils.bstack11l111l1ll_opy_ import bstack1ll1l11l11_opy_, bstack1l1ll1l1_opy_, bstack1l11ll1l11_opy_
from browserstack_sdk import sdk_pb2 as structs
class bstack1ll1ll111ll_opy_(bstack1l1lll11l1l_opy_):
    bstack1l11ll1ll1l_opy_ = bstack1111ll_opy_ (u"ࠨࡴࡦࡵࡷࡣࡩࡸࡩࡷࡧࡵࡷࠧጸ")
    bstack1l1ll1llll1_opy_ = bstack1111ll_opy_ (u"ࠢࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡸࠨጹ")
    bstack1l11ll1llll_opy_ = bstack1111ll_opy_ (u"ࠣࡰࡲࡲࡤࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡠࡵࡨࡷࡸ࡯࡯࡯ࡵࠥጺ")
    bstack1l11lll1l1l_opy_ = bstack1111ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࡴࠤጻ")
    bstack1l11llll1ll_opy_ = bstack1111ll_opy_ (u"ࠥࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴ࡟ࡪࡰࡶࡸࡦࡴࡣࡦࡡࡵࡩ࡫ࡹࠢጼ")
    bstack1l1l1lll1ll_opy_ = bstack1111ll_opy_ (u"ࠦࡨࡨࡴࡠࡵࡨࡷࡸ࡯࡯࡯ࡡࡦࡶࡪࡧࡴࡦࡦࠥጽ")
    bstack1l11llll111_opy_ = bstack1111ll_opy_ (u"ࠧࡩࡢࡵࡡࡶࡩࡸࡹࡩࡰࡰࡢࡲࡦࡳࡥࠣጾ")
    bstack1l11lllll11_opy_ = bstack1111ll_opy_ (u"ࠨࡣࡣࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡸࡺࡡࡵࡷࡶࠦጿ")
    def __init__(self):
        super().__init__(bstack1l1lll1llll_opy_=self.bstack1l11ll1ll1l_opy_, frameworks=[bstack1lll11lllll_opy_.NAME])
        if not self.is_enabled():
            return
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.BEFORE_EACH, bstack1lll1l111ll_opy_.POST), self.bstack1l11ll1lll1_opy_)
        if bstack1l1l11lll1_opy_():
            TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.POST), self.bstack1ll11l11l1l_opy_)
        else:
            TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.PRE), self.bstack1ll11l11l1l_opy_)
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.POST), self.bstack1ll11l1ll11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l11ll1lll1_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        bstack1l11lll1ll1_opy_ = self.bstack1l11lll1lll_opy_(instance.context)
        if not bstack1l11lll1ll1_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡴࡧࡷࡣࡦࡩࡴࡪࡸࡨࡣࡵࡧࡧࡦ࠼ࠣࡲࡴࠦࡰࡢࡩࡨࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࠧፀ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠣࠤፁ"))
            return
        f.bstack1lllll111ll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1ll1llll1_opy_, bstack1l11lll1ll1_opy_)
    def bstack1l11lll1lll_opy_(self, context: bstack1llllll1111_opy_, bstack1l11lll11l1_opy_= True):
        if bstack1l11lll11l1_opy_:
            bstack1l11lll1ll1_opy_ = self.bstack1l1llll1111_opy_(context, reverse=True)
        else:
            bstack1l11lll1ll1_opy_ = self.bstack1l1lll11lll_opy_(context, reverse=True)
        return [f for f in bstack1l11lll1ll1_opy_ if f[1].state != bstack1llll11llll_opy_.QUIT]
    def bstack1ll11l11l1l_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll1lll1_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if not bstack1l1l1llll11_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡲࡲࡤࡨࡥࡧࡱࡵࡩࡤࡺࡥࡴࡶ࠽ࠤࡳࡵࡴࠡࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠠࡴࡧࡶࡷ࡮ࡵ࡮ࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧፂ") + str(kwargs) + bstack1111ll_opy_ (u"ࠥࠦፃ"))
            return
        bstack1l11lll1ll1_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l11lll1ll1_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦࡴࡴ࡟ࡣࡧࡩࡳࡷ࡫࡟ࡵࡧࡶࡸ࠿ࠦ࡮ࡰࠢࡧࡶ࡮ࡼࡥࡳࡵࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢፄ") + str(kwargs) + bstack1111ll_opy_ (u"ࠧࠨፅ"))
            return
        if len(bstack1l11lll1ll1_opy_) > 1:
            self.logger.debug(
                bstack11111l1ll1_opy_ (u"ࠨ࡯࡯ࡡࡥࡩ࡫ࡵࡲࡦࡡࡷࡩࡸࡺ࠺ࠡࡽ࡯ࡩࡳ࠮ࡰࡢࡩࡨࡣ࡮ࡴࡳࡵࡣࡱࡧࡪࡹࠩࡾࠢࡧࡶ࡮ࡼࡥࡳࡵࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࡻ࡬ࡹࡤࡶ࡬ࡹࡽࠣፆ"))
        bstack1l11llll1l1_opy_, bstack1l1l11l1ll1_opy_ = bstack1l11lll1ll1_opy_[0]
        page = bstack1l11llll1l1_opy_()
        if not page:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡰࡰࡢࡦࡪ࡬࡯ࡳࡧࡢࡸࡪࡹࡴ࠻ࠢࡱࡳࠥࡶࡡࡨࡧࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢፇ") + str(kwargs) + bstack1111ll_opy_ (u"ࠣࠤፈ"))
            return
        bstack1l1l1l1ll1_opy_ = getattr(args[0], bstack1111ll_opy_ (u"ࠤࡱࡳࡩ࡫ࡩࡥࠤፉ"), None)
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1111ll_opy_ (u"ࠥࡸࡪࡹࡴࡄࡱࡱࡸࡪࡾࡴࡐࡲࡷ࡭ࡴࡴࡳࠣፊ")).get(bstack1111ll_opy_ (u"ࠦࡸࡱࡩࡱࡕࡨࡷࡸ࡯࡯࡯ࡐࡤࡱࡪࠨፋ")):
            try:
                page.evaluate(bstack1111ll_opy_ (u"ࠧࡥࠠ࠾ࡀࠣࡿࢂࠨፌ"),
                            bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤ࡫ࡸࡦࡥࡸࡸࡴࡸ࠺ࠡࡽࠥࡥࡨࡺࡩࡰࡰࠥ࠾ࠥࠨࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠢ࠭ࠢࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨ࠺ࠡࡽࠥࡲࡦࡳࡥࠣ࠼ࠪፍ") + json.dumps(
                                bstack1l1l1l1ll1_opy_) + bstack1111ll_opy_ (u"ࠢࡾࡿࠥፎ"))
            except Exception as e:
                self.logger.debug(bstack1111ll_opy_ (u"ࠣࡧࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡴࡡ࡮ࡧࠣࡿࢂࠨፏ"), e)
    def bstack1ll11l1ll11_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll1lll1_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if not bstack1l1l1llll11_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡲࡲࡤࡨࡥࡧࡱࡵࡩࡤࡺࡥࡴࡶ࠽ࠤࡳࡵࡴࠡࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠠࡴࡧࡶࡷ࡮ࡵ࡮ࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧፐ") + str(kwargs) + bstack1111ll_opy_ (u"ࠥࠦፑ"))
            return
        bstack1l11lll1ll1_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l11lll1ll1_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦࡴࡴ࡟ࡣࡧࡩࡳࡷ࡫࡟ࡵࡧࡶࡸ࠿ࠦ࡮ࡰࠢࡧࡶ࡮ࡼࡥࡳࡵࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢፒ") + str(kwargs) + bstack1111ll_opy_ (u"ࠧࠨፓ"))
            return
        if len(bstack1l11lll1ll1_opy_) > 1:
            self.logger.debug(
                bstack11111l1ll1_opy_ (u"ࠨ࡯࡯ࡡࡥࡩ࡫ࡵࡲࡦࡡࡷࡩࡸࡺ࠺ࠡࡽ࡯ࡩࡳ࠮ࡰࡢࡩࡨࡣ࡮ࡴࡳࡵࡣࡱࡧࡪࡹࠩࡾࠢࡧࡶ࡮ࡼࡥࡳࡵࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࡻ࡬ࡹࡤࡶ࡬ࡹࡽࠣፔ"))
        bstack1l11llll1l1_opy_, bstack1l1l11l1ll1_opy_ = bstack1l11lll1ll1_opy_[0]
        page = bstack1l11llll1l1_opy_()
        if not page:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡰࡰࡢࡦࡪ࡬࡯ࡳࡧࡢࡸࡪࡹࡴ࠻ࠢࡱࡳࠥࡶࡡࡨࡧࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢፕ") + str(kwargs) + bstack1111ll_opy_ (u"ࠣࠤፖ"))
            return
        status = f.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l11lll111l_opy_, None)
        if not status:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡱࡳࠥࡹࡴࡢࡶࡸࡷࠥ࡬࡯ࡳࠢࡷࡩࡸࡺࠬࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࠧፗ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠥࠦፘ"))
            return
        bstack1l11lll1111_opy_ = {bstack1111ll_opy_ (u"ࠦࡸࡺࡡࡵࡷࡶࠦፙ"): status.lower()}
        bstack1l11ll1ll11_opy_ = f.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l11lll1l11_opy_, None)
        if status.lower() == bstack1111ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬፚ") and bstack1l11ll1ll11_opy_ is not None:
            bstack1l11lll1111_opy_[bstack1111ll_opy_ (u"࠭ࡲࡦࡣࡶࡳࡳ࠭፛")] = bstack1l11ll1ll11_opy_[0][bstack1111ll_opy_ (u"ࠧࡣࡣࡦ࡯ࡹࡸࡡࡤࡧࠪ፜")][0] if isinstance(bstack1l11ll1ll11_opy_, list) else str(bstack1l11ll1ll11_opy_)
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1111ll_opy_ (u"ࠣࡶࡨࡷࡹࡉ࡯࡯ࡶࡨࡼࡹࡕࡰࡵ࡫ࡲࡲࡸࠨ፝")).get(bstack1111ll_opy_ (u"ࠤࡶ࡯࡮ࡶࡓࡦࡵࡶ࡭ࡴࡴࡓࡵࡣࡷࡹࡸࠨ፞")):
            try:
                page.evaluate(
                        bstack1111ll_opy_ (u"ࠥࡣࠥࡃ࠾ࠡࡽࢀࠦ፟"),
                        bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡩࡽ࡫ࡣࡶࡶࡲࡶ࠿ࠦࡻࠣࡣࡦࡸ࡮ࡵ࡮ࠣ࠼ࠣࠦࡸ࡫ࡴࡔࡧࡶࡷ࡮ࡵ࡮ࡔࡶࡤࡸࡺࡹࠢ࠭ࠢࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨ࠺ࠡࠩ፠")
                        + json.dumps(bstack1l11lll1111_opy_)
                        + bstack1111ll_opy_ (u"ࠧࢃࠢ፡")
                    )
            except Exception as e:
                self.logger.debug(bstack1111ll_opy_ (u"ࠨࡥࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠢࡶࡩࡸࡹࡩࡰࡰࠣࡷࡹࡧࡴࡶࡵࠣࡿࢂࠨ።"), e)
    def bstack1l1ll1111ll_opy_(
        self,
        instance: bstack1lll1llllll_opy_,
        f: TestFramework,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll1lll1_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if not bstack1l1l1llll11_opy_:
            self.logger.debug(
                bstack11111l1ll1_opy_ (u"ࠢ࡮ࡣࡵ࡯ࡤࡵ࠱࠲ࡻࡢࡷࡾࡴࡣ࠻ࠢࡱࡳࡹࠦࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠥࡹࡥࡴࡵ࡬ࡳࡳ࠲ࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࡻ࡬ࡹࡤࡶ࡬ࡹࡽࠣ፣"))
            return
        bstack1l11lll1ll1_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l11lll1ll1_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠣࡱࡱࡣࡧ࡫ࡦࡰࡴࡨࡣࡹ࡫ࡳࡵ࠼ࠣࡲࡴࠦࡤࡳ࡫ࡹࡩࡷࡹࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦ፤") + str(kwargs) + bstack1111ll_opy_ (u"ࠤࠥ፥"))
            return
        if len(bstack1l11lll1ll1_opy_) > 1:
            self.logger.debug(
                bstack11111l1ll1_opy_ (u"ࠥࡳࡳࡥࡢࡦࡨࡲࡶࡪࡥࡴࡦࡵࡷ࠾ࠥࢁ࡬ࡦࡰࠫࡴࡦ࡭ࡥࡠ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶ࠭ࢂࠦࡤࡳ࡫ࡹࡩࡷࡹࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࡿࡰࡽࡡࡳࡩࡶࢁࠧ፦"))
        bstack1l11llll1l1_opy_, bstack1l1l11l1ll1_opy_ = bstack1l11lll1ll1_opy_[0]
        page = bstack1l11llll1l1_opy_()
        if not page:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦࡲࡧࡲ࡬ࡡࡲ࠵࠶ࡿ࡟ࡴࡻࡱࡧ࠿ࠦ࡮ࡰࠢࡳࡥ࡬࡫ࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦ፧") + str(kwargs) + bstack1111ll_opy_ (u"ࠧࠨ፨"))
            return
        timestamp = int(time.time() * 1000)
        data = bstack1111ll_opy_ (u"ࠨࡏࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࡙ࡹ࡯ࡥ࠽ࠦ፩") + str(timestamp)
        try:
            page.evaluate(
                bstack1111ll_opy_ (u"ࠢࡠࠢࡀࡂࠥࢁࡽࠣ፪"),
                bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࢂ࠭፫").format(
                    json.dumps(
                        {
                            bstack1111ll_opy_ (u"ࠤࡤࡧࡹ࡯࡯࡯ࠤ፬"): bstack1111ll_opy_ (u"ࠥࡥࡳࡴ࡯ࡵࡣࡷࡩࠧ፭"),
                            bstack1111ll_opy_ (u"ࠦࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠢ፮"): {
                                bstack1111ll_opy_ (u"ࠧࡺࡹࡱࡧࠥ፯"): bstack1111ll_opy_ (u"ࠨࡁ࡯ࡰࡲࡸࡦࡺࡩࡰࡰࠥ፰"),
                                bstack1111ll_opy_ (u"ࠢࡥࡣࡷࡥࠧ፱"): data,
                                bstack1111ll_opy_ (u"ࠣ࡮ࡨࡺࡪࡲࠢ፲"): bstack1111ll_opy_ (u"ࠤࡧࡩࡧࡻࡧࠣ፳")
                            }
                        }
                    )
                )
            )
        except Exception as e:
            self.logger.debug(bstack1111ll_opy_ (u"ࠥࡩࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࠦ࡯࠲࠳ࡼࠤࡦࡴ࡮ࡰࡶࡤࡸ࡮ࡵ࡮ࠡ࡯ࡤࡶࡰ࡯࡮ࡨࠢࡾࢁࠧ፴"), e)
    def bstack1l1ll1ll11l_opy_(
        self,
        instance: bstack1lll1llllll_opy_,
        f: TestFramework,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll1lll1_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if f.bstack1llllll1lll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1l1lll1ll_opy_, False):
            return
        self.bstack1ll1111ll1l_opy_()
        req = structs.TestSessionEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll11ll1l11_opy_)
        req.test_framework_name = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll111lll11_opy_)
        req.test_framework_version = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l1l1ll1111_opy_)
        req.test_framework_state = bstack1llll1lll1l_opy_[0].name
        req.test_hook_state = bstack1llll1lll1l_opy_[1].name
        req.test_uuid = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll111l1lll_opy_)
        for bstack1l11ll1l1ll_opy_ in bstack1lll11ll111_opy_.bstack1llllll111l_opy_.values():
            session = req.automation_sessions.add()
            session.provider = (
                bstack1111ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠥ፵")
                if bstack1l1l1llll11_opy_
                else bstack1111ll_opy_ (u"ࠧࡻ࡮࡬ࡰࡲࡻࡳࡥࡧࡳ࡫ࡧࠦ፶")
            )
            session.ref = bstack1l11ll1l1ll_opy_.ref()
            session.hub_url = bstack1lll11ll111_opy_.bstack1llllll1lll_opy_(bstack1l11ll1l1ll_opy_, bstack1lll11ll111_opy_.bstack1l11lllll1l_opy_, bstack1111ll_opy_ (u"ࠨࠢ፷"))
            session.framework_name = bstack1l11ll1l1ll_opy_.framework_name
            session.framework_version = bstack1l11ll1l1ll_opy_.framework_version
            session.framework_session_id = bstack1lll11ll111_opy_.bstack1llllll1lll_opy_(bstack1l11ll1l1ll_opy_, bstack1lll11ll111_opy_.bstack1l11llllll1_opy_, bstack1111ll_opy_ (u"ࠢࠣ፸"))
        req.execution_context.hash = str(instance.context.hash)
        req.execution_context.thread_id = str(instance.context.thread_id)
        req.execution_context.process_id = str(instance.context.process_id)
        return req
    def bstack1ll11l1l111_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs
    ):
        bstack1l11lll1ll1_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1ll1ll111ll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l11lll1ll1_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠣࡩࡨࡸࡤࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡡࡧࡶ࡮ࡼࡥࡳ࠼ࠣࡲࡴࠦࡰࡢࡩࡨࡷࠥ࡬࡯ࡳࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࢁࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰࡿࠣࡥࡷ࡭ࡳ࠾ࡽࡤࡶ࡬ࡹࡽࠡ࡭ࡺࡥࡷ࡭ࡳ࠾ࠤ፹") + str(kwargs) + bstack1111ll_opy_ (u"ࠤࠥ፺"))
            return
        if len(bstack1l11lll1ll1_opy_) > 1:
            self.logger.debug(bstack1111ll_opy_ (u"ࠥ࡫ࡪࡺ࡟ࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡣࡩࡸࡩࡷࡧࡵ࠾ࠥࢁ࡬ࡦࡰࠫࡴࡦ࡭ࡥࡠ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶ࠭ࢂࠦࡤࡳ࡫ࡹࡩࡷࡹࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦ፻") + str(kwargs) + bstack1111ll_opy_ (u"ࠦࠧ፼"))
        bstack1l11llll1l1_opy_, bstack1l1l11l1ll1_opy_ = bstack1l11lll1ll1_opy_[0]
        page = bstack1l11llll1l1_opy_()
        if not page:
            self.logger.debug(bstack1111ll_opy_ (u"ࠧ࡭ࡥࡵࡡࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡥࡤࡳ࡫ࡹࡩࡷࡀࠠ࡯ࡱࠣࡴࡦ࡭ࡥࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧ፽") + str(kwargs) + bstack1111ll_opy_ (u"ࠨࠢ፾"))
            return
        return page
    def bstack1ll111111ll_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs
    ):
        caps = {}
        bstack1l11lll11ll_opy_ = {}
        for bstack1l11ll1l1ll_opy_ in bstack1lll11ll111_opy_.bstack1llllll111l_opy_.values():
            caps = bstack1lll11ll111_opy_.bstack1llllll1lll_opy_(bstack1l11ll1l1ll_opy_, bstack1lll11ll111_opy_.bstack1l1l1111l1l_opy_, bstack1111ll_opy_ (u"ࠢࠣ፿"))
        bstack1l11lll11ll_opy_[bstack1111ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡐࡤࡱࡪࠨᎀ")] = caps.get(bstack1111ll_opy_ (u"ࠤࡥࡶࡴࡽࡳࡦࡴࠥᎁ"), bstack1111ll_opy_ (u"ࠥࠦᎂ"))
        bstack1l11lll11ll_opy_[bstack1111ll_opy_ (u"ࠦࡵࡲࡡࡵࡨࡲࡶࡲࡔࡡ࡮ࡧࠥᎃ")] = caps.get(bstack1111ll_opy_ (u"ࠧࡵࡳࠣᎄ"), bstack1111ll_opy_ (u"ࠨࠢᎅ"))
        bstack1l11lll11ll_opy_[bstack1111ll_opy_ (u"ࠢࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠤᎆ")] = caps.get(bstack1111ll_opy_ (u"ࠣࡱࡶࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠧᎇ"), bstack1111ll_opy_ (u"ࠤࠥᎈ"))
        bstack1l11lll11ll_opy_[bstack1111ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠦᎉ")] = caps.get(bstack1111ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡤࡼࡥࡳࡵ࡬ࡳࡳࠨᎊ"), bstack1111ll_opy_ (u"ࠧࠨᎋ"))
        return bstack1l11lll11ll_opy_
    def bstack1ll11ll1ll1_opy_(self, page: object, bstack1ll1111lll1_opy_, args={}):
        try:
            bstack1l11llll11l_opy_ = bstack1111ll_opy_ (u"ࠨࠢࠣࠪࡩࡹࡳࡩࡴࡪࡱࡱࠤ࠭࠴࠮࠯ࡤࡶࡸࡦࡩ࡫ࡔࡦ࡮ࡅࡷ࡭ࡳࠪࠢࡾࡿࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡳࡧࡷࡹࡷࡴࠠ࡯ࡧࡺࠤࡕࡸ࡯࡮࡫ࡶࡩ࠭࠮ࡲࡦࡵࡲࡰࡻ࡫ࠬࠡࡴࡨ࡮ࡪࡩࡴࠪࠢࡀࡂࠥࢁࡻࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡣࡵࡷࡥࡨࡱࡓࡥ࡭ࡄࡶ࡬ࡹ࠮ࡱࡷࡶ࡬࠭ࡸࡥࡴࡱ࡯ࡺࡪ࠯࠻ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡼࡨࡱࡣࡧࡵࡤࡺࡿࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࢃࡽࠪ࠽ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡿࢀ࠭࠭ࢁࡡࡳࡩࡢ࡮ࡸࡵ࡮ࡾࠫࠥࠦࠧᎌ")
            bstack1ll1111lll1_opy_ = bstack1ll1111lll1_opy_.replace(bstack1111ll_opy_ (u"ࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥᎍ"), bstack1111ll_opy_ (u"ࠣࡤࡶࡸࡦࡩ࡫ࡔࡦ࡮ࡅࡷ࡭ࡳࠣᎎ"))
            script = bstack1l11llll11l_opy_.format(fn_body=bstack1ll1111lll1_opy_, arg_json=json.dumps(args))
            return page.evaluate(script)
        except Exception as e:
            self.logger.error(bstack1111ll_opy_ (u"ࠤࡤ࠵࠶ࡿ࡟ࡴࡥࡵ࡭ࡵࡺ࡟ࡦࡺࡨࡧࡺࡺࡥ࠻ࠢࡈࡶࡷࡵࡲࠡࡧࡻࡩࡨࡻࡴࡪࡰࡪࠤࡹ࡮ࡥࠡࡣ࠴࠵ࡾࠦࡳࡤࡴ࡬ࡴࡹ࠲ࠠࠣᎏ") + str(e) + bstack1111ll_opy_ (u"ࠥࠦ᎐"))