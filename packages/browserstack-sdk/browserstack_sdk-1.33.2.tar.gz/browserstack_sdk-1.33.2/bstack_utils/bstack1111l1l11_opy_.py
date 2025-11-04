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
import json
from bstack_utils.bstack1lll1llll1_opy_ import get_logger
logger = get_logger(__name__)
class bstack11ll111l1l1_opy_(object):
  bstack111l1111_opy_ = os.path.join(os.path.expanduser(bstack1111ll_opy_ (u"ࠨࢀࠪ᝷")), bstack1111ll_opy_ (u"ࠩ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠩ᝸"))
  bstack11ll111l1ll_opy_ = os.path.join(bstack111l1111_opy_, bstack1111ll_opy_ (u"ࠪࡧࡴࡳ࡭ࡢࡰࡧࡷ࠳ࡰࡳࡰࡰࠪ᝹"))
  commands_to_wrap = None
  perform_scan = None
  bstack1lll11lll_opy_ = None
  bstack1llll1llll_opy_ = None
  bstack11ll1l11l1l_opy_ = None
  bstack11ll1l111ll_opy_ = None
  def __new__(cls):
    if not hasattr(cls, bstack1111ll_opy_ (u"ࠫ࡮ࡴࡳࡵࡣࡱࡧࡪ࠭᝺")):
      cls.instance = super(bstack11ll111l1l1_opy_, cls).__new__(cls)
      cls.instance.bstack11ll111l11l_opy_()
    return cls.instance
  def bstack11ll111l11l_opy_(self):
    try:
      with open(self.bstack11ll111l1ll_opy_, bstack1111ll_opy_ (u"ࠬࡸࠧ᝻")) as bstack111lll1ll1_opy_:
        bstack11ll111l111_opy_ = bstack111lll1ll1_opy_.read()
        data = json.loads(bstack11ll111l111_opy_)
        if bstack1111ll_opy_ (u"࠭ࡣࡰ࡯ࡰࡥࡳࡪࡳࠨ᝼") in data:
          self.bstack11ll1l1ll1l_opy_(data[bstack1111ll_opy_ (u"ࠧࡤࡱࡰࡱࡦࡴࡤࡴࠩ᝽")])
        if bstack1111ll_opy_ (u"ࠨࡵࡦࡶ࡮ࡶࡴࡴࠩ᝾") in data:
          self.bstack11ll1llll_opy_(data[bstack1111ll_opy_ (u"ࠩࡶࡧࡷ࡯ࡰࡵࡵࠪ᝿")])
        if bstack1111ll_opy_ (u"ࠪࡲࡴࡴࡂࡔࡶࡤࡧࡰࡏ࡮ࡧࡴࡤࡅ࠶࠷ࡹࡄࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧក") in data:
          self.bstack11ll111ll11_opy_(data[bstack1111ll_opy_ (u"ࠫࡳࡵ࡮ࡃࡕࡷࡥࡨࡱࡉ࡯ࡨࡵࡥࡆ࠷࠱ࡺࡅ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨខ")])
    except:
      pass
  def bstack11ll111ll11_opy_(self, bstack11ll1l111ll_opy_):
    if bstack11ll1l111ll_opy_ != None:
      self.bstack11ll1l111ll_opy_ = bstack11ll1l111ll_opy_
  def bstack11ll1llll_opy_(self, scripts):
    if scripts != None:
      self.perform_scan = scripts.get(bstack1111ll_opy_ (u"ࠬࡹࡣࡢࡰࠪគ"),bstack1111ll_opy_ (u"࠭ࠧឃ"))
      self.bstack1lll11lll_opy_ = scripts.get(bstack1111ll_opy_ (u"ࠧࡨࡧࡷࡖࡪࡹࡵ࡭ࡶࡶࠫង"),bstack1111ll_opy_ (u"ࠨࠩច"))
      self.bstack1llll1llll_opy_ = scripts.get(bstack1111ll_opy_ (u"ࠩࡪࡩࡹࡘࡥࡴࡷ࡯ࡸࡸ࡙ࡵ࡮࡯ࡤࡶࡾ࠭ឆ"),bstack1111ll_opy_ (u"ࠪࠫជ"))
      self.bstack11ll1l11l1l_opy_ = scripts.get(bstack1111ll_opy_ (u"ࠫࡸࡧࡶࡦࡔࡨࡷࡺࡲࡴࡴࠩឈ"),bstack1111ll_opy_ (u"ࠬ࠭ញ"))
  def bstack11ll1l1ll1l_opy_(self, commands_to_wrap):
    if commands_to_wrap != None and len(commands_to_wrap) != 0:
      self.commands_to_wrap = commands_to_wrap
  def store(self):
    try:
      with open(self.bstack11ll111l1ll_opy_, bstack1111ll_opy_ (u"࠭ࡷࠨដ")) as file:
        json.dump({
          bstack1111ll_opy_ (u"ࠢࡤࡱࡰࡱࡦࡴࡤࡴࠤឋ"): self.commands_to_wrap,
          bstack1111ll_opy_ (u"ࠣࡵࡦࡶ࡮ࡶࡴࡴࠤឌ"): {
            bstack1111ll_opy_ (u"ࠤࡶࡧࡦࡴࠢឍ"): self.perform_scan,
            bstack1111ll_opy_ (u"ࠥ࡫ࡪࡺࡒࡦࡵࡸࡰࡹࡹࠢណ"): self.bstack1lll11lll_opy_,
            bstack1111ll_opy_ (u"ࠦ࡬࡫ࡴࡓࡧࡶࡹࡱࡺࡳࡔࡷࡰࡱࡦࡸࡹࠣត"): self.bstack1llll1llll_opy_,
            bstack1111ll_opy_ (u"ࠧࡹࡡࡷࡧࡕࡩࡸࡻ࡬ࡵࡵࠥថ"): self.bstack11ll1l11l1l_opy_
          },
          bstack1111ll_opy_ (u"ࠨ࡮ࡰࡰࡅࡗࡹࡧࡣ࡬ࡋࡱࡪࡷࡧࡁ࠲࠳ࡼࡇ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠥទ"): self.bstack11ll1l111ll_opy_
        }, file)
    except Exception as e:
      logger.error(bstack1111ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡷࡩ࡫࡯ࡩࠥࡹࡴࡰࡴ࡬ࡲ࡬ࠦࡣࡰ࡯ࡰࡥࡳࡪࡳ࠻ࠢࡾࢁࠧធ").format(e))
      pass
  def bstack11l1l111_opy_(self, command_name):
    try:
      return any(command.get(bstack1111ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭ន")) == command_name for command in self.commands_to_wrap)
    except:
      return False
bstack1111l1l11_opy_ = bstack11ll111l1l1_opy_()