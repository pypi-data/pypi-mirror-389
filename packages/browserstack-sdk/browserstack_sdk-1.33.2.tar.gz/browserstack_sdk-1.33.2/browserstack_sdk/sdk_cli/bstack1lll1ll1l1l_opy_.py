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
from datetime import datetime, timezone
from browserstack_sdk.sdk_cli.bstack1llllll1l1l_opy_ import (
    bstack1llll11llll_opy_,
    bstack1lllll1lll1_opy_,
    bstack1llll1llll1_opy_,
    bstack1lllll1111l_opy_,
    bstack1llllll1111_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll1lllll1_opy_ import bstack1lll11lllll_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_, bstack1lll1llllll_opy_
from browserstack_sdk.sdk_cli.bstack1l1lll1l1ll_opy_ import bstack1l1lll11l1l_opy_
from typing import Tuple, Dict, Any, List, Union
from bstack_utils.helper import bstack1l1l1llll11_opy_
from browserstack_sdk import sdk_pb2 as structs
from bstack_utils.measure import measure
from bstack_utils.constants import *
from typing import Tuple, List, Any
class bstack1lll1111lll_opy_(bstack1l1lll11l1l_opy_):
    bstack1l11ll1ll1l_opy_ = bstack1111ll_opy_ (u"ࠢࡵࡧࡶࡸࡤࡪࡲࡪࡸࡨࡶࡸࠨᏨ")
    bstack1l1ll1llll1_opy_ = bstack1111ll_opy_ (u"ࠣࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡤࡹࡥࡴࡵ࡬ࡳࡳࡹࠢᏩ")
    bstack1l11ll1llll_opy_ = bstack1111ll_opy_ (u"ࠤࡱࡳࡳࡥࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡡࡶࡩࡸࡹࡩࡰࡰࡶࠦᏪ")
    bstack1l11lll1l1l_opy_ = bstack1111ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡵࡨࡷࡸ࡯࡯࡯ࡵࠥᏫ")
    bstack1l11llll1ll_opy_ = bstack1111ll_opy_ (u"ࠦࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡠ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡢࡶࡪ࡬ࡳࠣᏬ")
    bstack1l1l1lll1ll_opy_ = bstack1111ll_opy_ (u"ࠧࡩࡢࡵࡡࡶࡩࡸࡹࡩࡰࡰࡢࡧࡷ࡫ࡡࡵࡧࡧࠦᏭ")
    bstack1l11llll111_opy_ = bstack1111ll_opy_ (u"ࠨࡣࡣࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡳࡧ࡭ࡦࠤᏮ")
    bstack1l11lllll11_opy_ = bstack1111ll_opy_ (u"ࠢࡤࡤࡷࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡤࡹࡴࡢࡶࡸࡷࠧᏯ")
    def __init__(self):
        super().__init__(bstack1l1lll1llll_opy_=self.bstack1l11ll1ll1l_opy_, frameworks=[bstack1lll11lllll_opy_.NAME])
        if not self.is_enabled():
            return
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.BEFORE_EACH, bstack1lll1l111ll_opy_.POST), self.bstack1l11l11ll11_opy_)
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.PRE), self.bstack1ll11l11l1l_opy_)
        TestFramework.bstack1ll111ll1l1_opy_((bstack1ll1l11lll1_opy_.TEST, bstack1lll1l111ll_opy_.POST), self.bstack1ll11l1ll11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l11l11ll11_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        bstack1l1lll11111_opy_ = self.bstack1l11l111lll_opy_(instance.context)
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠣࡵࡨࡸࡤࡧࡣࡵ࡫ࡹࡩࡤࡪࡲࡪࡸࡨࡶࡸࡀࠠ࡯ࡱࠣࡨࡷ࡯ࡶࡦࡴࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࠦᏰ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠤࠥᏱ"))
        f.bstack1lllll111ll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, bstack1l1lll11111_opy_)
        bstack1l11l1111l1_opy_ = self.bstack1l11l111lll_opy_(instance.context, bstack1l11l1111ll_opy_=False)
        f.bstack1lllll111ll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11ll1llll_opy_, bstack1l11l1111l1_opy_)
    def bstack1ll11l11l1l_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11l11ll11_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if not f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11llll111_opy_, False):
            self.__1l11l111l11_opy_(f,instance,bstack1llll1lll1l_opy_)
    def bstack1ll11l1ll11_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11l11ll11_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        if not f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11llll111_opy_, False):
            self.__1l11l111l11_opy_(f, instance, bstack1llll1lll1l_opy_)
        if not f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11lllll11_opy_, False):
            self.__1l11l11l1ll_opy_(f, instance, bstack1llll1lll1l_opy_)
    def bstack1l11l11l1l1_opy_(
        self,
        f: bstack1lll11lllll_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance = exec[0]
        if not f.bstack1l1lll1l11l_opy_(instance):
            return
        if f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11lllll11_opy_, False):
            return
        driver.execute_script(
            bstack1111ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࡽࠣᏲ").format(
                json.dumps(
                    {
                        bstack1111ll_opy_ (u"ࠦࡦࡩࡴࡪࡱࡱࠦᏳ"): bstack1111ll_opy_ (u"ࠧࡹࡥࡵࡕࡨࡷࡸ࡯࡯࡯ࡕࡷࡥࡹࡻࡳࠣᏴ"),
                        bstack1111ll_opy_ (u"ࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤᏵ"): {bstack1111ll_opy_ (u"ࠢࡴࡶࡤࡸࡺࡹࠢ᏶"): result},
                    }
                )
            )
        )
        f.bstack1lllll111ll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11lllll11_opy_, True)
    def bstack1l11l111lll_opy_(self, context: bstack1llllll1111_opy_, bstack1l11l1111ll_opy_= True):
        if bstack1l11l1111ll_opy_:
            bstack1l1lll11111_opy_ = self.bstack1l1llll1111_opy_(context, reverse=True)
        else:
            bstack1l1lll11111_opy_ = self.bstack1l1lll11lll_opy_(context, reverse=True)
        return [f for f in bstack1l1lll11111_opy_ if f[1].state != bstack1llll11llll_opy_.QUIT]
    @measure(event_name=EVENTS.bstack1l1111l111_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
    def __1l11l11l1ll_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
    ):
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1111ll_opy_ (u"ࠣࡶࡨࡷࡹࡉ࡯࡯ࡶࡨࡼࡹࡕࡰࡵ࡫ࡲࡲࡸࠨ᏷")).get(bstack1111ll_opy_ (u"ࠤࡶ࡯࡮ࡶࡓࡦࡵࡶ࡭ࡴࡴࡓࡵࡣࡷࡹࡸࠨᏸ")):
            bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
            if not bstack1l1lll11111_opy_:
                self.logger.debug(bstack1111ll_opy_ (u"ࠥࡷࡪࡺ࡟ࡢࡥࡷ࡭ࡻ࡫࡟ࡥࡴ࡬ࡺࡪࡸࡳ࠻ࠢࡱࡳࠥࡪࡲࡪࡸࡨࡶࠥ࡬࡯ࡳࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࠨᏹ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠦࠧᏺ"))
                return
            driver = bstack1l1lll11111_opy_[0][0]()
            status = f.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l11lll111l_opy_, None)
            if not status:
                self.logger.debug(bstack1111ll_opy_ (u"ࠧࡹࡥࡵࡡࡤࡧࡹ࡯ࡶࡦࡡࡧࡶ࡮ࡼࡥࡳࡵ࠽ࠤࡳࡵࠠࡴࡶࡤࡸࡺࡹࠠࡧࡱࡵࠤࡹ࡫ࡳࡵ࠮ࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࠢᏻ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠨࠢᏼ"))
                return
            bstack1l11lll1111_opy_ = {bstack1111ll_opy_ (u"ࠢࡴࡶࡤࡸࡺࡹࠢᏽ"): status.lower()}
            bstack1l11ll1ll11_opy_ = f.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l11lll1l11_opy_, None)
            if status.lower() == bstack1111ll_opy_ (u"ࠨࡨࡤ࡭ࡱ࡫ࡤࠨ᏾") and bstack1l11ll1ll11_opy_ is not None:
                bstack1l11lll1111_opy_[bstack1111ll_opy_ (u"ࠩࡵࡩࡦࡹ࡯࡯ࠩ᏿")] = bstack1l11ll1ll11_opy_[0][bstack1111ll_opy_ (u"ࠪࡦࡦࡩ࡫ࡵࡴࡤࡧࡪ࠭᐀")][0] if isinstance(bstack1l11ll1ll11_opy_, list) else str(bstack1l11ll1ll11_opy_)
            driver.execute_script(
                bstack1111ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡩࡽ࡫ࡣࡶࡶࡲࡶ࠿ࠦࡻࡾࠤᐁ").format(
                    json.dumps(
                        {
                            bstack1111ll_opy_ (u"ࠧࡧࡣࡵ࡫ࡲࡲࠧᐂ"): bstack1111ll_opy_ (u"ࠨࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡖࡸࡦࡺࡵࡴࠤᐃ"),
                            bstack1111ll_opy_ (u"ࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥᐄ"): bstack1l11lll1111_opy_,
                        }
                    )
                )
            )
            f.bstack1lllll111ll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11lllll11_opy_, True)
    @measure(event_name=EVENTS.bstack1l1111ll11_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
    def __1l11l111l11_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_]
    ):
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1111ll_opy_ (u"ࠣࡶࡨࡷࡹࡉ࡯࡯ࡶࡨࡼࡹࡕࡰࡵ࡫ࡲࡲࡸࠨᐅ")).get(bstack1111ll_opy_ (u"ࠤࡶ࡯࡮ࡶࡓࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠦᐆ")):
            test_name = f.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l11l11l11l_opy_, None)
            if not test_name:
                self.logger.debug(bstack1111ll_opy_ (u"ࠥࡳࡳࡥࡢࡦࡨࡲࡶࡪࡥࡴࡦࡵࡷ࠾ࠥࡳࡩࡴࡵ࡬ࡲ࡬ࠦࡴࡦࡵࡷࠤࡳࡧ࡭ࡦࠤᐇ"))
                return
            bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
            if not bstack1l1lll11111_opy_:
                self.logger.debug(bstack1111ll_opy_ (u"ࠦࡸ࡫ࡴࡠࡣࡦࡸ࡮ࡼࡥࡠࡦࡵ࡭ࡻ࡫ࡲࡴ࠼ࠣࡲࡴࠦࡳࡵࡣࡷࡹࡸࠦࡦࡰࡴࠣࡸࡪࡹࡴ࠭ࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࠨᐈ") + str(bstack1llll1lll1l_opy_) + bstack1111ll_opy_ (u"ࠧࠨᐉ"))
                return
            for bstack1l1l11l1111_opy_, bstack1l11l11ll1l_opy_ in bstack1l1lll11111_opy_:
                if not bstack1lll11lllll_opy_.bstack1l1lll1l11l_opy_(bstack1l11l11ll1l_opy_):
                    continue
                driver = bstack1l1l11l1111_opy_()
                if not driver:
                    continue
                driver.execute_script(
                    bstack1111ll_opy_ (u"ࠨࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤ࡫ࡸࡦࡥࡸࡸࡴࡸ࠺ࠡࡽࢀࠦᐊ").format(
                        json.dumps(
                            {
                                bstack1111ll_opy_ (u"ࠢࡢࡥࡷ࡭ࡴࡴࠢᐋ"): bstack1111ll_opy_ (u"ࠣࡵࡨࡸࡘ࡫ࡳࡴ࡫ࡲࡲࡓࡧ࡭ࡦࠤᐌ"),
                                bstack1111ll_opy_ (u"ࠤࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠧᐍ"): {bstack1111ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᐎ"): test_name},
                            }
                        )
                    )
                )
            f.bstack1lllll111ll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11llll111_opy_, True)
    def bstack1l1ll1111ll_opy_(
        self,
        instance: bstack1lll1llllll_opy_,
        f: TestFramework,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11l11ll11_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        bstack1l1lll11111_opy_ = [d for d, _ in f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])]
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦࡴࡴ࡟ࡢࡨࡷࡩࡷࡥࡴࡦࡵࡷ࠾ࠥࡴ࡯ࠡࡵࡨࡷࡸ࡯࡯࡯ࡵࠣࡸࡴࠦ࡬ࡪࡰ࡮ࠦᐏ"))
            return
        if not bstack1l1l1llll11_opy_():
            self.logger.debug(bstack1111ll_opy_ (u"ࠧࡵ࡮ࡠࡣࡩࡸࡪࡸ࡟ࡵࡧࡶࡸ࠿ࠦ࡮ࡰࡶࠣࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠢࡶࡩࡸࡹࡩࡰࡰࠥᐐ"))
            return
        for bstack1l11l111l1l_opy_ in bstack1l1lll11111_opy_:
            driver = bstack1l11l111l1l_opy_()
            if not driver:
                continue
            timestamp = int(time.time() * 1000)
            data = bstack1111ll_opy_ (u"ࠨࡏࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࡙ࡹ࡯ࡥ࠽ࠦᐑ") + str(timestamp)
            driver.execute_script(
                bstack1111ll_opy_ (u"ࠢࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲ࠻ࠢࡾࢁࠧᐒ").format(
                    json.dumps(
                        {
                            bstack1111ll_opy_ (u"ࠣࡣࡦࡸ࡮ࡵ࡮ࠣᐓ"): bstack1111ll_opy_ (u"ࠤࡤࡲࡳࡵࡴࡢࡶࡨࠦᐔ"),
                            bstack1111ll_opy_ (u"ࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨᐕ"): {
                                bstack1111ll_opy_ (u"ࠦࡹࡿࡰࡦࠤᐖ"): bstack1111ll_opy_ (u"ࠧࡇ࡮࡯ࡱࡷࡥࡹ࡯࡯࡯ࠤᐗ"),
                                bstack1111ll_opy_ (u"ࠨࡤࡢࡶࡤࠦᐘ"): data,
                                bstack1111ll_opy_ (u"ࠢ࡭ࡧࡹࡩࡱࠨᐙ"): bstack1111ll_opy_ (u"ࠣࡦࡨࡦࡺ࡭ࠢᐚ")
                            }
                        }
                    )
                )
            )
    def bstack1l1ll1ll11l_opy_(
        self,
        instance: bstack1lll1llllll_opy_,
        f: TestFramework,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11l11ll11_opy_(f, instance, bstack1llll1lll1l_opy_, *args, **kwargs)
        keys = [
            bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_,
            bstack1lll1111lll_opy_.bstack1l11ll1llll_opy_,
        ]
        bstack1l1lll11111_opy_ = []
        for key in keys:
            bstack1l1lll11111_opy_.extend(f.bstack1llllll1lll_opy_(instance, key, []))
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡲࡲࡤࡧࡦࡵࡧࡵࡣࡹ࡫ࡳࡵ࠼ࠣࡹࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡦࡪࡰࡧࠤࡦࡴࡹࠡࡵࡨࡷࡸ࡯࡯࡯ࡵࠣࡸࡴࠦ࡬ࡪࡰ࡮ࠦᐛ"))
            return
        if f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1l1lll1ll_opy_, False):
            self.logger.debug(bstack1111ll_opy_ (u"ࠥࡳࡳࡥࡡࡧࡶࡨࡶࡤࡺࡥࡴࡶ࠽ࠤࡈࡈࡔࠡࡣ࡯ࡶࡪࡧࡤࡺࠢࡦࡶࡪࡧࡴࡦࡦࠥᐜ"))
            return
        self.bstack1ll1111ll1l_opy_()
        bstack1l1l1l1l11_opy_ = datetime.now()
        req = structs.TestSessionEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll11ll1l11_opy_)
        req.test_framework_name = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll111lll11_opy_)
        req.test_framework_version = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l1l1ll1111_opy_)
        req.test_framework_state = bstack1llll1lll1l_opy_[0].name
        req.test_hook_state = bstack1llll1lll1l_opy_[1].name
        req.test_uuid = TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1ll111l1lll_opy_)
        for bstack1l1l11l1111_opy_, driver in bstack1l1lll11111_opy_:
            try:
                webdriver = bstack1l1l11l1111_opy_()
                if webdriver is None:
                    self.logger.debug(bstack1111ll_opy_ (u"ࠦ࡜࡫ࡢࡅࡴ࡬ࡺࡪࡸࠠࡪࡰࡶࡸࡦࡴࡣࡦࠢ࡬ࡷࠥࡔ࡯࡯ࡧࠣࠬࡷ࡫ࡦࡦࡴࡨࡲࡨ࡫ࠠࡦࡺࡳ࡭ࡷ࡫ࡤࠪࠤᐝ"))
                    continue
                session = req.automation_sessions.add()
                session.provider = (
                    bstack1111ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠦᐞ")
                    if bstack1lll11lllll_opy_.bstack1llllll1lll_opy_(driver, bstack1lll11lllll_opy_.bstack1l11l11l111_opy_, False)
                    else bstack1111ll_opy_ (u"ࠨࡵ࡯࡭ࡱࡳࡼࡴ࡟ࡨࡴ࡬ࡨࠧᐟ")
                )
                session.ref = driver.ref()
                session.hub_url = bstack1lll11lllll_opy_.bstack1llllll1lll_opy_(driver, bstack1lll11lllll_opy_.bstack1l11lllll1l_opy_, bstack1111ll_opy_ (u"ࠢࠣᐠ"))
                session.framework_name = driver.framework_name
                session.framework_version = driver.framework_version
                session.framework_session_id = bstack1lll11lllll_opy_.bstack1llllll1lll_opy_(driver, bstack1lll11lllll_opy_.bstack1l11llllll1_opy_, bstack1111ll_opy_ (u"ࠣࠤᐡ"))
                caps = None
                if hasattr(webdriver, bstack1111ll_opy_ (u"ࠤࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠣᐢ")):
                    try:
                        caps = webdriver.capabilities
                        self.logger.debug(bstack1111ll_opy_ (u"ࠥࡗࡺࡩࡣࡦࡵࡶࡪࡺࡲ࡬ࡺࠢࡵࡩࡹࡸࡩࡦࡸࡨࡨࠥࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠤࡩ࡯ࡲࡦࡥࡷࡰࡾࠦࡦࡳࡱࡰࠤࡩࡸࡩࡷࡧࡵ࠲ࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡩࡦࡵࠥᐣ"))
                    except Exception as e:
                        self.logger.debug(bstack1111ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡨࡧࡷࠤࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡩࡦࡵࠣࡪࡷࡵ࡭ࠡࡦࡵ࡭ࡻ࡫ࡲ࠯ࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹ࠺ࠡࠤᐤ") + str(e) + bstack1111ll_opy_ (u"ࠧࠨᐥ"))
                try:
                    bstack1l11l111ll1_opy_ = json.dumps(caps).encode(bstack1111ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧᐦ")) if caps else bstack1l11l11lll1_opy_ (u"ࠢࡼࡿࠥᐧ")
                    req.capabilities = bstack1l11l111ll1_opy_
                except Exception as e:
                    self.logger.debug(bstack1111ll_opy_ (u"ࠣࡩࡨࡸࡤࡩࡢࡵࡡࡨࡺࡪࡴࡴ࠻ࠢࡩࡥ࡮ࡲࡥࡥࠢࡷࡳࠥࡹࡥ࡯ࡦࠣࡷࡪࡸࡩࡢ࡮࡬ࡾࡪࠦࡣࡢࡲࡶࠤ࡫ࡵࡲࠡࡴࡨࡵࡺ࡫ࡳࡵ࠼ࠣࠦᐨ") + str(e) + bstack1111ll_opy_ (u"ࠤࠥᐩ"))
            except Exception as e:
                self.logger.error(bstack1111ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢࡳࡶࡴࡩࡥࡴࡵ࡬ࡲ࡬ࠦࡤࡳ࡫ࡹࡩࡷࠦࡩࡵࡧࡰ࠾ࠥࠨᐪ") + str(str(e)) + bstack1111ll_opy_ (u"ࠦࠧᐫ"))
        req.execution_context.hash = str(instance.context.hash)
        req.execution_context.thread_id = str(instance.context.thread_id)
        req.execution_context.process_id = str(instance.context.process_id)
        return req
    def bstack1ll111111ll_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs
    ):
        bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l1l1llll11_opy_() and len(bstack1l1lll11111_opy_) == 0:
            bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11ll1llll_opy_, [])
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠧࡵ࡮ࡠࡤࡨࡪࡴࡸࡥࡠࡶࡨࡷࡹࡀࠠ࡯ࡱࠣࡨࡷ࡯ࡶࡦࡴࡶࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣᐬ") + str(kwargs) + bstack1111ll_opy_ (u"ࠨࠢᐭ"))
            return {}
        if len(bstack1l1lll11111_opy_) > 1:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡰࡰࡢࡦࡪ࡬࡯ࡳࡧࡢࡸࡪࡹࡴ࠻ࠢࡾࡰࡪࡴࠨࡥࡴ࡬ࡺࡪࡸ࡟ࡪࡰࡶࡸࡦࡴࡣࡦࡵࠬࢁࠥࡪࡲࡪࡸࡨࡶࡸࠦࡦࡰࡴࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࡻࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࢀࠤࡦࡸࡧࡴ࠿ࡾࡥࡷ࡭ࡳࡾࠢ࡮ࡻࡦࡸࡧࡴ࠿ࠥᐮ") + str(kwargs) + bstack1111ll_opy_ (u"ࠣࠤᐯ"))
            return {}
        bstack1l1l11l1111_opy_, bstack1l1l11l1ll1_opy_ = bstack1l1lll11111_opy_[0]
        driver = bstack1l1l11l1111_opy_()
        if not driver:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡲࡲࡤࡨࡥࡧࡱࡵࡩࡤࡺࡥࡴࡶ࠽ࠤࡳࡵࠠࡥࡴ࡬ࡺࡪࡸࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦᐰ") + str(kwargs) + bstack1111ll_opy_ (u"ࠥࠦᐱ"))
            return {}
        capabilities = f.bstack1llllll1lll_opy_(bstack1l1l11l1ll1_opy_, bstack1lll11lllll_opy_.bstack1l1l1111l1l_opy_)
        if not capabilities:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦࡴࡴ࡟ࡣࡧࡩࡳࡷ࡫࡟ࡵࡧࡶࡸ࠿ࠦ࡮ࡰࠢࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠡࡨࡲࡹࡳࡪࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦᐲ") + str(kwargs) + bstack1111ll_opy_ (u"ࠧࠨᐳ"))
            return {}
        return capabilities.get(bstack1111ll_opy_ (u"ࠨࡡ࡭ࡹࡤࡽࡸࡓࡡࡵࡥ࡫ࠦᐴ"), {})
    def bstack1ll11l1l111_opy_(
        self,
        f: TestFramework,
        instance: bstack1lll1llllll_opy_,
        bstack1llll1lll1l_opy_: Tuple[bstack1ll1l11lll1_opy_, bstack1lll1l111ll_opy_],
        *args,
        **kwargs
    ):
        bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l1ll1llll1_opy_, [])
        if not bstack1l1l1llll11_opy_() and len(bstack1l1lll11111_opy_) == 0:
            bstack1l1lll11111_opy_ = f.bstack1llllll1lll_opy_(instance, bstack1lll1111lll_opy_.bstack1l11ll1llll_opy_, [])
        if not bstack1l1lll11111_opy_:
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡨࡧࡷࡣࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡠࡦࡵ࡭ࡻ࡫ࡲ࠻ࠢࡱࡳࠥࡪࡲࡪࡸࡨࡶࡸࠦࡦࡰࡴࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࡻࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࢀࠤࡦࡸࡧࡴ࠿ࡾࡥࡷ࡭ࡳࡾࠢ࡮ࡻࡦࡸࡧࡴ࠿ࠥᐵ") + str(kwargs) + bstack1111ll_opy_ (u"ࠣࠤᐶ"))
            return
        if len(bstack1l1lll11111_opy_) > 1:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡪࡩࡹࡥࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࡢࡨࡷ࡯ࡶࡦࡴ࠽ࠤࢀࡲࡥ࡯ࠪࡧࡶ࡮ࡼࡥࡳࡡ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡷ࠮ࢃࠠࡥࡴ࡬ࡺࡪࡸࡳࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧᐷ") + str(kwargs) + bstack1111ll_opy_ (u"ࠥࠦᐸ"))
        bstack1l1l11l1111_opy_, bstack1l1l11l1ll1_opy_ = bstack1l1lll11111_opy_[0]
        driver = bstack1l1l11l1111_opy_()
        if not driver:
            self.logger.debug(bstack1111ll_opy_ (u"ࠦ࡬࡫ࡴࡠࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡤࡪࡲࡪࡸࡨࡶ࠿ࠦ࡮ࡰࠢࡧࡶ࡮ࡼࡥࡳࠢࡩࡳࡷࠦࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰ࠿ࡾ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࢃࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨᐹ") + str(kwargs) + bstack1111ll_opy_ (u"ࠧࠨᐺ"))
            return
        return driver