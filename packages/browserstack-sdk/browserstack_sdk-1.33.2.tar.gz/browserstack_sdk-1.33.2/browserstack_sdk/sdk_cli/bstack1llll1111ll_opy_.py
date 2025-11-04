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
from browserstack_sdk.sdk_cli.bstack1ll1ll1llll_opy_ import bstack1ll1lll111l_opy_
from browserstack_sdk.sdk_cli.bstack1llllll1l1l_opy_ import (
    bstack1llll11llll_opy_,
    bstack1lllll1lll1_opy_,
    bstack1lllll1111l_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll1lllll1_opy_ import bstack1lll11lllll_opy_
from typing import Tuple, Callable, Any
import grpc
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.bstack1ll1ll1llll_opy_ import bstack1ll1lll111l_opy_
from bstack_utils.measure import measure
from bstack_utils.constants import *
import traceback
import os
import time
class bstack1ll1l1l11l1_opy_(bstack1ll1lll111l_opy_):
    bstack1ll111l1l11_opy_ = False
    def __init__(self):
        super().__init__()
        bstack1lll11lllll_opy_.bstack1ll111ll1l1_opy_((bstack1llll11llll_opy_.bstack1lllll11ll1_opy_, bstack1lllll1lll1_opy_.PRE), self.bstack1l1llll11l1_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l1llll11l1_opy_(
        self,
        f: bstack1lll11lllll_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        hub_url = f.hub_url(driver)
        if f.bstack1l1llll1l11_opy_(hub_url):
            if not bstack1ll1l1l11l1_opy_.bstack1ll111l1l11_opy_:
                self.logger.warning(bstack1111ll_opy_ (u"ࠤ࡯ࡳࡨࡧ࡬ࠡࡵࡨࡰ࡫࠳ࡨࡦࡣ࡯ࠤ࡫ࡲ࡯ࡸࠢࡧ࡭ࡸࡧࡢ࡭ࡧࡧࠤ࡫ࡵࡲࠡࡄࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࠠࡪࡰࡩࡶࡦࠦࡳࡦࡵࡶ࡭ࡴࡴࡳࠡࡪࡸࡦࡤࡻࡲ࡭࠿ࠥቍ") + str(hub_url) + bstack1111ll_opy_ (u"ࠥࠦ቎"))
                bstack1ll1l1l11l1_opy_.bstack1ll111l1l11_opy_ = True
            return
        command_name = f.bstack1ll1111llll_opy_(*args)
        bstack1l1llll1lll_opy_ = f.bstack1l1lllll111_opy_(*args)
        if command_name and command_name.lower() == bstack1111ll_opy_ (u"ࠦ࡫࡯࡮ࡥࡧ࡯ࡩࡲ࡫࡮ࡵࠤ቏") and bstack1l1llll1lll_opy_:
            framework_session_id = f.session_id(driver)
            locator_type, locator_value = bstack1l1llll1lll_opy_.get(bstack1111ll_opy_ (u"ࠧࡻࡳࡪࡰࡪࠦቐ"), None), bstack1l1llll1lll_opy_.get(bstack1111ll_opy_ (u"ࠨࡶࡢ࡮ࡸࡩࠧቑ"), None)
            if not framework_session_id or not locator_type or not locator_value:
                self.logger.warning(bstack1111ll_opy_ (u"ࠢࡼࡥࡲࡱࡲࡧ࡮ࡥࡡࡱࡥࡲ࡫ࡽ࠻ࠢࡰ࡭ࡸࡹࡩ࡯ࡩࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡳࡦࡵࡶ࡭ࡴࡴ࡟ࡪࡦࠣࡳࡷࠦࡡࡳࡩࡶ࠲ࡺࡹࡩ࡯ࡩࡀࡿࡱࡵࡣࡢࡶࡲࡶࡤࡺࡹࡱࡧࢀࠤࡴࡸࠠࡢࡴࡪࡷ࠳ࡼࡡ࡭ࡷࡨࡁࠧቒ") + str(locator_value) + bstack1111ll_opy_ (u"ࠣࠤቓ"))
                return
            def bstack1lllll11l11_opy_(driver, bstack1l1lllll11l_opy_, *args, **kwargs):
                from selenium.common.exceptions import NoSuchElementException
                try:
                    result = bstack1l1lllll11l_opy_(driver, *args, **kwargs)
                    response = self.bstack1l1lllll1ll_opy_(
                        framework_session_id=framework_session_id,
                        is_success=True,
                        locator_type=locator_type,
                        locator_value=locator_value,
                    )
                    if response and response.execute_script:
                        driver.execute_script(response.execute_script)
                        self.logger.info(bstack1111ll_opy_ (u"ࠤࡶࡹࡨࡩࡥࡴࡵ࠰ࡷࡨࡸࡩࡱࡶ࠽ࠤࡱࡵࡣࡢࡶࡲࡶࡤࡺࡹࡱࡧࡀࡿࡱࡵࡣࡢࡶࡲࡶࡤࡺࡹࡱࡧࢀࠤࡱࡵࡣࡢࡶࡲࡶࡤࡼࡡ࡭ࡷࡨࡁࠧቔ") + str(locator_value) + bstack1111ll_opy_ (u"ࠥࠦቕ"))
                    else:
                        self.logger.warning(bstack1111ll_opy_ (u"ࠦࡸࡻࡣࡤࡧࡶࡷ࠲ࡴ࡯࠮ࡵࡦࡶ࡮ࡶࡴ࠻ࠢ࡯ࡳࡨࡧࡴࡰࡴࡢࡸࡾࡶࡥ࠾ࡽ࡯ࡳࡨࡧࡴࡰࡴࡢࡸࡾࡶࡥࡾࠢ࡯ࡳࡨࡧࡴࡰࡴࡢࡺࡦࡲࡵࡦ࠿ࡾࡰࡴࡩࡡࡵࡱࡵࡣࡻࡧ࡬ࡶࡧࢀࠤࡷ࡫ࡳࡱࡱࡱࡷࡪࡃࠢቖ") + str(response) + bstack1111ll_opy_ (u"ࠧࠨ቗"))
                    return result
                except NoSuchElementException as e:
                    locator = (locator_type, locator_value)
                    return self.__1l1llll11ll_opy_(
                        driver, bstack1l1lllll11l_opy_, e, framework_session_id, locator, *args, **kwargs
                    )
            bstack1lllll11l11_opy_.__name__ = command_name
            return bstack1lllll11l11_opy_
    def __1l1llll11ll_opy_(
        self,
        driver,
        bstack1l1lllll11l_opy_: Callable,
        exception,
        framework_session_id: str,
        locator: Tuple[str, str],
        *args,
        **kwargs,
    ):
        try:
            locator_type, locator_value = locator
            response = self.bstack1l1lllll1ll_opy_(
                framework_session_id=framework_session_id,
                is_success=False,
                locator_type=locator_type,
                locator_value=locator_value,
            )
            if response and response.execute_script:
                driver.execute_script(response.execute_script)
                self.logger.info(bstack1111ll_opy_ (u"ࠨࡦࡢ࡫࡯ࡹࡷ࡫࠭ࡩࡧࡤࡰ࡮ࡴࡧ࠮ࡶࡵ࡭࡬࡭ࡥࡳࡧࡧ࠾ࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࢁࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡶࡢ࡮ࡸࡩࡂࠨቘ") + str(locator_value) + bstack1111ll_opy_ (u"ࠢࠣ቙"))
                bstack1l1llll1l1l_opy_ = self.bstack1l1lllll1l1_opy_(
                    framework_session_id=framework_session_id,
                    locator_type=locator_type,
                )
                self.logger.info(bstack1111ll_opy_ (u"ࠣࡨࡤ࡭ࡱࡻࡲࡦ࠯࡫ࡩࡦࡲࡩ࡯ࡩ࠰ࡶࡪࡹࡵ࡭ࡶ࠽ࠤࡱࡵࡣࡢࡶࡲࡶࡤࡺࡹࡱࡧࡀࡿࡱࡵࡣࡢࡶࡲࡶࡤࡺࡹࡱࡧࢀࠤࡱࡵࡣࡢࡶࡲࡶࡤࡼࡡ࡭ࡷࡨࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡶࡢ࡮ࡸࡩࢂࠦࡨࡦࡣ࡯࡭ࡳ࡭࡟ࡳࡧࡶࡹࡱࡺ࠽ࠣቚ") + str(bstack1l1llll1l1l_opy_) + bstack1111ll_opy_ (u"ࠤࠥቛ"))
                if bstack1l1llll1l1l_opy_.success and args and len(args) > 1:
                    args[1].update(
                        {
                            bstack1111ll_opy_ (u"ࠥࡹࡸ࡯࡮ࡨࠤቜ"): bstack1l1llll1l1l_opy_.locator_type,
                            bstack1111ll_opy_ (u"ࠦࡻࡧ࡬ࡶࡧࠥቝ"): bstack1l1llll1l1l_opy_.locator_value,
                        }
                    )
                    return bstack1l1lllll11l_opy_(driver, *args, **kwargs)
                elif os.environ.get(bstack1111ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡆࡏ࡟ࡅࡇࡅ࡙ࡌࠨ቞"), False):
                    self.logger.info(bstack11111l1ll1_opy_ (u"ࠨࡦࡢ࡫࡯ࡹࡷ࡫࠭ࡩࡧࡤࡰ࡮ࡴࡧ࠮ࡴࡨࡷࡺࡲࡴ࠮࡯࡬ࡷࡸ࡯࡮ࡨ࠼ࠣࡷࡱ࡫ࡥࡱࠪ࠶࠴࠮ࠦ࡬ࡦࡶࡷ࡭ࡳ࡭ࠠࡺࡱࡸࠤ࡮ࡴࡳࡱࡧࡦࡸࠥࡺࡨࡦࠢࡥࡶࡴࡽࡳࡦࡴࠣࡩࡽࡺࡥ࡯ࡵ࡬ࡳࡳࠦ࡬ࡰࡩࡶࠦ቟"))
                    time.sleep(300)
            else:
                self.logger.warning(bstack1111ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡺࡸࡥ࠮ࡰࡲ࠱ࡸࡩࡲࡪࡲࡷ࠾ࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࢁࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡶࡢ࡮ࡸࡩࡂࢁ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡷࡣ࡯ࡹࡪࢃࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠿ࠥበ") + str(response) + bstack1111ll_opy_ (u"ࠣࠤቡ"))
        except Exception as err:
            self.logger.warning(bstack1111ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡵࡳࡧ࠰࡬ࡪࡧ࡬ࡪࡰࡪ࠱ࡷ࡫ࡳࡶ࡮ࡷ࠾ࠥ࡫ࡲࡳࡱࡵ࠾ࠥࠨቢ") + str(err) + bstack1111ll_opy_ (u"ࠥࠦባ"))
        raise exception
    @measure(event_name=EVENTS.bstack1l1llll1ll1_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
    def bstack1l1lllll1ll_opy_(
        self,
        framework_session_id: str,
        is_success: bool,
        locator_type: str,
        locator_value: str,
        platform_index=bstack1111ll_opy_ (u"ࠦ࠵ࠨቤ"),
    ):
        self.bstack1ll1111ll1l_opy_()
        req = structs.AISelfHealStepRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_session_id = framework_session_id
        req.is_success = is_success
        req.test_name = bstack1111ll_opy_ (u"ࠧࠨብ")
        req.locator_type = locator_type
        req.locator_value = locator_value
        try:
            r = self.bstack1lll11ll1l1_opy_.AISelfHealStep(req)
            self.logger.info(bstack1111ll_opy_ (u"ࠨࡲࡦࡥࡨ࡭ࡻ࡫ࡤࠡࡨࡵࡳࡲࠦࡳࡦࡴࡹࡩࡷࡀࠠࠣቦ") + str(r) + bstack1111ll_opy_ (u"ࠢࠣቧ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1111ll_opy_ (u"ࠣࡴࡳࡧ࠲࡫ࡲࡳࡱࡵ࠾ࠥࠨቨ") + str(e) + bstack1111ll_opy_ (u"ࠤࠥቩ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l1llllll11_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
    def bstack1l1lllll1l1_opy_(self, framework_session_id: str, locator_type: str, platform_index=bstack1111ll_opy_ (u"ࠥ࠴ࠧቪ")):
        self.bstack1ll1111ll1l_opy_()
        req = structs.AISelfHealGetRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_session_id = framework_session_id
        req.locator_type = locator_type
        try:
            r = self.bstack1lll11ll1l1_opy_.AISelfHealGetResult(req)
            self.logger.info(bstack1111ll_opy_ (u"ࠦࡷ࡫ࡣࡦ࡫ࡹࡩࡩࠦࡦࡳࡱࡰࠤࡸ࡫ࡲࡷࡧࡵ࠾ࠥࠨቫ") + str(r) + bstack1111ll_opy_ (u"ࠧࠨቬ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1111ll_opy_ (u"ࠨࡲࡱࡥ࠰ࡩࡷࡸ࡯ࡳ࠼ࠣࠦቭ") + str(e) + bstack1111ll_opy_ (u"ࠢࠣቮ"))
            traceback.print_exc()
            raise e