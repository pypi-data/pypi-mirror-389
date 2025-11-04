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
    bstack1llll1llll1_opy_,
    bstack1lllll1111l_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll1lllll1_opy_ import bstack1lll11lllll_opy_
from browserstack_sdk.sdk_cli.bstack1lll1ll1lll_opy_ import bstack1lll11ll111_opy_
from browserstack_sdk.sdk_cli.bstack1llll1l1111_opy_ import bstack1llllll1111_opy_
from typing import Tuple, Dict, Any, List, Callable
from browserstack_sdk.sdk_cli.bstack1ll1ll1llll_opy_ import bstack1ll1lll111l_opy_
import weakref
class bstack1l1lll11l1l_opy_(bstack1ll1lll111l_opy_):
    bstack1l1lll1llll_opy_: str
    frameworks: List[str]
    drivers: Dict[str, Tuple[Callable, bstack1lllll1111l_opy_]]
    pages: Dict[str, Tuple[Callable, bstack1lllll1111l_opy_]]
    def __init__(self, bstack1l1lll1llll_opy_: str, frameworks: List[str]):
        super().__init__()
        self.drivers = dict()
        self.pages = dict()
        self.bstack1l1lll1lll1_opy_ = dict()
        self.bstack1l1lll1llll_opy_ = bstack1l1lll1llll_opy_
        self.frameworks = frameworks
        bstack1lll11ll111_opy_.bstack1ll111ll1l1_opy_((bstack1llll11llll_opy_.bstack1lllll11lll_opy_, bstack1lllll1lll1_opy_.POST), self.__1l1lll1ll1l_opy_)
        if any(bstack1lll11lllll_opy_.NAME in f.lower().strip() for f in frameworks):
            bstack1lll11lllll_opy_.bstack1ll111ll1l1_opy_(
                (bstack1llll11llll_opy_.bstack1lllll11ll1_opy_, bstack1lllll1lll1_opy_.PRE), self.__1l1lll11ll1_opy_
            )
            bstack1lll11lllll_opy_.bstack1ll111ll1l1_opy_(
                (bstack1llll11llll_opy_.QUIT, bstack1lllll1lll1_opy_.POST), self.__1l1lll1l1l1_opy_
            )
    def __1l1lll1ll1l_opy_(
        self,
        f: bstack1lll11ll111_opy_,
        bstack1l1lll1l111_opy_: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        try:
            instance, method_name = exec
            if method_name != bstack1111ll_opy_ (u"ࠦࡳ࡫ࡷࡠࡲࡤ࡫ࡪࠨቲ"):
                return
            contexts = bstack1l1lll1l111_opy_.browser.contexts
            if contexts:
                for context in contexts:
                    if context.pages:
                        for page in context.pages:
                            if bstack1111ll_opy_ (u"ࠧࡧࡢࡰࡷࡷ࠾ࡧࡲࡡ࡯࡭ࠥታ") in page.url:
                                self.logger.debug(bstack1111ll_opy_ (u"ࠨࡓࡵࡱࡵ࡭ࡳ࡭ࠠࡵࡪࡨࠤࡳ࡫ࡷࠡࡲࡤ࡫ࡪࠦࡩ࡯ࡵࡷࡥࡳࡩࡥࠣቴ"))
                                self.pages[instance.ref()] = weakref.ref(page), instance
                                bstack1llll1llll1_opy_.bstack1lllll111ll_opy_(instance, self.bstack1l1lll1llll_opy_, True)
                                self.logger.debug(bstack1111ll_opy_ (u"ࠢࡠࡡࡲࡲࡤࡶࡡࡨࡧࡢ࡭ࡳ࡯ࡴ࠻ࠢ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡁࠧት") + str(instance.ref()) + bstack1111ll_opy_ (u"ࠣࠤቶ"))
        except Exception as e:
            self.logger.debug(bstack1111ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡵࡷࡳࡷ࡯࡮ࡨࠢࡱࡩࡼࠦࡰࡢࡩࡨࠤ࠿ࠨቷ"),e)
    def __1l1lll11ll1_opy_(
        self,
        f: bstack1lll11lllll_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if instance.ref() in self.drivers or bstack1llll1llll1_opy_.bstack1llllll1lll_opy_(instance, self.bstack1l1lll1llll_opy_, False):
            return
        if not f.bstack1l1llll1l11_opy_(f.hub_url(driver)):
            self.bstack1l1lll1lll1_opy_[instance.ref()] = weakref.ref(driver), instance
            bstack1llll1llll1_opy_.bstack1lllll111ll_opy_(instance, self.bstack1l1lll1llll_opy_, True)
            self.logger.debug(bstack1111ll_opy_ (u"ࠥࡣࡤࡵ࡮ࡠࡵࡨࡰࡪࡴࡩࡶ࡯ࡢ࡭ࡳ࡯ࡴ࠻ࠢࡱࡳࡳࡥࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤࡪࡲࡪࡸࡨࡶࠥ࡯࡮ࡴࡶࡤࡲࡨ࡫࠽ࠣቸ") + str(instance.ref()) + bstack1111ll_opy_ (u"ࠦࠧቹ"))
            return
        self.drivers[instance.ref()] = weakref.ref(driver), instance
        bstack1llll1llll1_opy_.bstack1lllll111ll_opy_(instance, self.bstack1l1lll1llll_opy_, True)
        self.logger.debug(bstack1111ll_opy_ (u"ࠧࡥ࡟ࡰࡰࡢࡷࡪࡲࡥ࡯࡫ࡸࡱࡤ࡯࡮ࡪࡶ࠽ࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࠢቺ") + str(instance.ref()) + bstack1111ll_opy_ (u"ࠨࠢቻ"))
    def __1l1lll1l1l1_opy_(
        self,
        f: bstack1lll11lllll_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1111l_opy_, str],
        bstack1llll1lll1l_opy_: Tuple[bstack1llll11llll_opy_, bstack1lllll1lll1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if not instance.ref() in self.drivers:
            return
        self.bstack1l1lll11l11_opy_(instance)
        self.logger.debug(bstack1111ll_opy_ (u"ࠢࡠࡡࡲࡲࡤࡹࡥ࡭ࡧࡱ࡭ࡺࡳ࡟ࡲࡷ࡬ࡸ࠿ࠦࡩ࡯ࡵࡷࡥࡳࡩࡥ࠾ࠤቼ") + str(instance.ref()) + bstack1111ll_opy_ (u"ࠣࠤች"))
    def bstack1l1llll1111_opy_(self, context: bstack1llllll1111_opy_, reverse=True) -> List[Tuple[Callable, bstack1lllll1111l_opy_]]:
        matches = []
        if self.pages:
            for data in self.pages.values():
                if data[1].bstack1l1llll111l_opy_(context):
                    matches.append(data)
        if self.drivers:
            for data in self.drivers.values():
                if (
                    bstack1lll11lllll_opy_.bstack1l1lll1l11l_opy_(data[1])
                    and data[1].bstack1l1llll111l_opy_(context)
                    and getattr(data[0](), bstack1111ll_opy_ (u"ࠤࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩࠨቾ"), False)
                ):
                    matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1lllll1ll11_opy_, reverse=reverse)
    def bstack1l1lll11lll_opy_(self, context: bstack1llllll1111_opy_, reverse=True) -> List[Tuple[Callable, bstack1lllll1111l_opy_]]:
        matches = []
        for data in self.bstack1l1lll1lll1_opy_.values():
            if (
                data[1].bstack1l1llll111l_opy_(context)
                and getattr(data[0](), bstack1111ll_opy_ (u"ࠥࡷࡪࡹࡳࡪࡱࡱࡣ࡮ࡪࠢቿ"), False)
            ):
                matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1lllll1ll11_opy_, reverse=reverse)
    def bstack1l1lll1ll11_opy_(self, instance: bstack1lllll1111l_opy_) -> bool:
        return instance and instance.ref() in self.drivers
    def bstack1l1lll11l11_opy_(self, instance: bstack1lllll1111l_opy_) -> bool:
        if self.bstack1l1lll1ll11_opy_(instance):
            self.drivers.pop(instance.ref())
            bstack1llll1llll1_opy_.bstack1lllll111ll_opy_(instance, self.bstack1l1lll1llll_opy_, False)
            return True
        return False