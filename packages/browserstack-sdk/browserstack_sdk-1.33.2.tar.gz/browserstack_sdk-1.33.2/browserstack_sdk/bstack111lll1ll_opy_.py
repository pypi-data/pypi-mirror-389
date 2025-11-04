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
import multiprocessing
import os
from bstack_utils.config import Config
class bstack11lll1111_opy_():
  def __init__(self, args, logger, bstack111111l11l_opy_, bstack111111l111_opy_, bstack1111111l1l_opy_):
    self.args = args
    self.logger = logger
    self.bstack111111l11l_opy_ = bstack111111l11l_opy_
    self.bstack111111l111_opy_ = bstack111111l111_opy_
    self.bstack1111111l1l_opy_ = bstack1111111l1l_opy_
  def bstack1llll1l111_opy_(self, bstack11111l1lll_opy_, bstack1lll11l1l1_opy_, bstack1111111l11_opy_=False):
    bstack11l1111lll_opy_ = []
    manager = multiprocessing.Manager()
    bstack11111ll1l1_opy_ = manager.list()
    bstack1l1l11ll11_opy_ = Config.bstack111l11ll1_opy_()
    if bstack1111111l11_opy_:
      for index, platform in enumerate(self.bstack111111l11l_opy_[bstack1111ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ႜ")]):
        if index == 0:
          bstack1lll11l1l1_opy_[bstack1111ll_opy_ (u"ࠫ࡫࡯࡬ࡦࡡࡱࡥࡲ࡫ࠧႝ")] = self.args
        bstack11l1111lll_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack11111l1lll_opy_,
                                                    args=(bstack1lll11l1l1_opy_, bstack11111ll1l1_opy_)))
    else:
      for index, platform in enumerate(self.bstack111111l11l_opy_[bstack1111ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨ႞")]):
        bstack11l1111lll_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack11111l1lll_opy_,
                                                    args=(bstack1lll11l1l1_opy_, bstack11111ll1l1_opy_)))
    i = 0
    for t in bstack11l1111lll_opy_:
      try:
        if bstack1l1l11ll11_opy_.get_property(bstack1111ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡥࡳࡦࡵࡶ࡭ࡴࡴࠧ႟")):
          os.environ[bstack1111ll_opy_ (u"ࠧࡄࡗࡕࡖࡊࡔࡔࡠࡒࡏࡅ࡙ࡌࡏࡓࡏࡢࡈࡆ࡚ࡁࠨႠ")] = json.dumps(self.bstack111111l11l_opy_[bstack1111ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫႡ")][i % self.bstack1111111l1l_opy_])
      except Exception as e:
        self.logger.debug(bstack1111ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡹ࡫࡭ࡱ࡫ࠠࡴࡶࡲࡶ࡮ࡴࡧࠡࡥࡸࡶࡷ࡫࡮ࡵࠢࡳࡰࡦࡺࡦࡰࡴࡰࠤࡩ࡫ࡴࡢ࡫࡯ࡷ࠿ࠦࡻࡾࠤႢ").format(str(e)))
      i += 1
      t.start()
    for t in bstack11l1111lll_opy_:
      t.join()
    return list(bstack11111ll1l1_opy_)