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
class bstack1llllll11_opy_:
    def __init__(self, handler):
        self._1lllll111lll_opy_ = None
        self.handler = handler
        self._1lllll111ll1_opy_ = self.bstack1lllll11l111_opy_()
        self.patch()
    def patch(self):
        self._1lllll111lll_opy_ = self._1lllll111ll1_opy_.execute
        self._1lllll111ll1_opy_.execute = self.bstack1lllll11l11l_opy_()
    def bstack1lllll11l11l_opy_(self):
        def execute(this, driver_command, *args, **kwargs):
            self.handler(bstack1111ll_opy_ (u"ࠢࡣࡧࡩࡳࡷ࡫ࠢ⁋"), driver_command, None, this, args)
            response = self._1lllll111lll_opy_(this, driver_command, *args, **kwargs)
            self.handler(bstack1111ll_opy_ (u"ࠣࡣࡩࡸࡪࡸࠢ⁌"), driver_command, response)
            return response
        return execute
    def reset(self):
        self._1lllll111ll1_opy_.execute = self._1lllll111lll_opy_
    @staticmethod
    def bstack1lllll11l111_opy_():
        from selenium.webdriver.remote.webdriver import WebDriver
        return WebDriver