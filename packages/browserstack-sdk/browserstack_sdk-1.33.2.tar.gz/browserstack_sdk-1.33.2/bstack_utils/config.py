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
conf = {
    bstack1111ll_opy_ (u"࠭ࡡࡱࡲࡢࡥࡺࡺ࡯࡮ࡣࡷࡩࠬ឴"): False,
    bstack1111ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠨ឵"): True,
    bstack1111ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡥࡳࡦࡵࡶ࡭ࡴࡴ࡟ࡴࡶࡤࡸࡺࡹࠧា"): False
}
class Config(object):
    instance = None
    def __init__(self):
        self._11l1lll1ll1_opy_ = conf
    @classmethod
    def bstack111l11ll1_opy_(cls):
        if cls.instance:
            return cls.instance
        return Config()
    def get_property(self, property_name, bstack11l1lll1l1l_opy_=None):
        return self._11l1lll1ll1_opy_.get(property_name, bstack11l1lll1l1l_opy_)
    def bstack1lll11llll_opy_(self, property_name, bstack11l1lll1l11_opy_):
        self._11l1lll1ll1_opy_[property_name] = bstack11l1lll1l11_opy_
    def bstack1l111llll_opy_(self, val):
        self._11l1lll1ll1_opy_[bstack1111ll_opy_ (u"ࠩࡶ࡯࡮ࡶ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࡠࡵࡷࡥࡹࡻࡳࠨិ")] = bool(val)
    def bstack11111ll111_opy_(self):
        return self._11l1lll1ll1_opy_.get(bstack1111ll_opy_ (u"ࠪࡷࡰ࡯ࡰࡠࡵࡨࡷࡸ࡯࡯࡯ࡡࡶࡸࡦࡺࡵࡴࠩី"), False)