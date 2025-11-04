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
class RobotHandler():
    def __init__(self, args, logger, bstack111111l11l_opy_, bstack111111l111_opy_):
        self.args = args
        self.logger = logger
        self.bstack111111l11l_opy_ = bstack111111l11l_opy_
        self.bstack111111l111_opy_ = bstack111111l111_opy_
    @staticmethod
    def version():
        import robot
        return robot.__version__
    @staticmethod
    def bstack111l111l11_opy_(bstack111111111l_opy_):
        bstack1111111111_opy_ = []
        if bstack111111111l_opy_:
            tokens = str(os.path.basename(bstack111111111l_opy_)).split(bstack1111ll_opy_ (u"ࠥࡣࠧႣ"))
            camelcase_name = bstack1111ll_opy_ (u"ࠦࠥࠨႤ").join(t.title() for t in tokens)
            suite_name, bstack11111111l1_opy_ = os.path.splitext(camelcase_name)
            bstack1111111111_opy_.append(suite_name)
        return bstack1111111111_opy_
    @staticmethod
    def bstack11111111ll_opy_(typename):
        if bstack1111ll_opy_ (u"ࠧࡇࡳࡴࡧࡵࡸ࡮ࡵ࡮ࠣႥ") in typename:
            return bstack1111ll_opy_ (u"ࠨࡁࡴࡵࡨࡶࡹ࡯࡯࡯ࡇࡵࡶࡴࡸࠢႦ")
        return bstack1111ll_opy_ (u"ࠢࡖࡰ࡫ࡥࡳࡪ࡬ࡦࡦࡈࡶࡷࡵࡲࠣႧ")