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
import logging
import datetime
import threading
from bstack_utils.helper import bstack11ll1l1lll1_opy_, bstack11ll1l1lll_opy_, get_host_info, bstack11l1111llll_opy_, \
 bstack1l1l111l1_opy_, bstack1l1l11ll1l_opy_, error_handler, bstack11l111l111l_opy_, bstack1ll1l11ll1_opy_
import bstack_utils.accessibility as bstack1l1111lll_opy_
from bstack_utils.bstack1l1ll1111_opy_ import bstack11l111ll_opy_
from bstack_utils.bstack111ll11lll_opy_ import bstack1ll1l111l1_opy_
from bstack_utils.percy import bstack1lll1l1l_opy_
from bstack_utils.config import Config
bstack1l1l11ll11_opy_ = Config.bstack111l11ll1_opy_()
logger = logging.getLogger(__name__)
percy = bstack1lll1l1l_opy_()
@error_handler(class_method=False)
def bstack1llll11ll1l1_opy_(bs_config, bstack1lll111l11_opy_):
  try:
    data = {
        bstack1111ll_opy_ (u"ࠬ࡬࡯ࡳ࡯ࡤࡸࠬ∂"): bstack1111ll_opy_ (u"࠭ࡪࡴࡱࡱࠫ∃"),
        bstack1111ll_opy_ (u"ࠧࡱࡴࡲ࡮ࡪࡩࡴࡠࡰࡤࡱࡪ࠭∄"): bs_config.get(bstack1111ll_opy_ (u"ࠨࡲࡵࡳ࡯࡫ࡣࡵࡐࡤࡱࡪ࠭∅"), bstack1111ll_opy_ (u"ࠩࠪ∆")),
        bstack1111ll_opy_ (u"ࠪࡲࡦࡳࡥࠨ∇"): bs_config.get(bstack1111ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧ∈"), os.path.basename(os.path.abspath(os.getcwd()))),
        bstack1111ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡣ࡮ࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ∉"): bs_config.get(bstack1111ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ∊")),
        bstack1111ll_opy_ (u"ࠧࡥࡧࡶࡧࡷ࡯ࡰࡵ࡫ࡲࡲࠬ∋"): bs_config.get(bstack1111ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡄࡦࡵࡦࡶ࡮ࡶࡴࡪࡱࡱࠫ∌"), bstack1111ll_opy_ (u"ࠩࠪ∍")),
        bstack1111ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࡧࡧࡣࡦࡺࠧ∎"): bstack1ll1l11ll1_opy_(),
        bstack1111ll_opy_ (u"ࠫࡹࡧࡧࡴࠩ∏"): bstack11l1111llll_opy_(bs_config),
        bstack1111ll_opy_ (u"ࠬ࡮࡯ࡴࡶࡢ࡭ࡳ࡬࡯ࠨ∐"): get_host_info(),
        bstack1111ll_opy_ (u"࠭ࡣࡪࡡ࡬ࡲ࡫ࡵࠧ∑"): bstack11ll1l1lll_opy_(),
        bstack1111ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡥࡲࡶࡰࡢ࡭ࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧ−"): os.environ.get(bstack1111ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡗࡌࡐࡉࡥࡒࡖࡐࡢࡍࡉࡋࡎࡕࡋࡉࡍࡊࡘࠧ∓")),
        bstack1111ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࡡࡷࡩࡸࡺࡳࡠࡴࡨࡶࡺࡴࠧ∔"): os.environ.get(bstack1111ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡕࡉࡗ࡛ࡎࠨ∕"), False),
        bstack1111ll_opy_ (u"ࠫࡻ࡫ࡲࡴ࡫ࡲࡲࡤࡩ࡯࡯ࡶࡵࡳࡱ࠭∖"): bstack11ll1l1lll1_opy_(),
        bstack1111ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ∗"): bstack1lll1llll1l1_opy_(bs_config),
        bstack1111ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡧࡩࡹࡧࡩ࡭ࡵࠪ∘"): bstack1llll11111l1_opy_(bstack1lll111l11_opy_),
        bstack1111ll_opy_ (u"ࠧࡱࡴࡲࡨࡺࡩࡴࡠ࡯ࡤࡴࠬ∙"): bstack1llll11111ll_opy_(bs_config, bstack1lll111l11_opy_.get(bstack1111ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡺࡹࡥࡥࠩ√"), bstack1111ll_opy_ (u"ࠩࠪ∛"))),
        bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠬ∜"): bstack1l1l111l1_opy_(bs_config),
        bstack1111ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࠩ∝"): bstack1lll1llll111_opy_(bs_config)
    }
    return data
  except Exception as error:
    logger.error(bstack1111ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡹ࡫࡭ࡱ࡫ࠠࡤࡴࡨࡥࡹ࡯࡮ࡨࠢࡳࡥࡾࡲ࡯ࡢࡦࠣࡪࡴࡸࠠࡕࡧࡶࡸࡍࡻࡢ࠻ࠢࠣࡿࢂࠨ∞").format(str(error)))
    return None
def bstack1llll11111l1_opy_(framework):
  return {
    bstack1111ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡐࡤࡱࡪ࠭∟"): framework.get(bstack1111ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥࠨ∠"), bstack1111ll_opy_ (u"ࠨࡒࡼࡸࡪࡹࡴࠨ∡")),
    bstack1111ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯࡛࡫ࡲࡴ࡫ࡲࡲࠬ∢"): framework.get(bstack1111ll_opy_ (u"ࠪࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡶࡦࡴࡶ࡭ࡴࡴࠧ∣")),
    bstack1111ll_opy_ (u"ࠫࡸࡪ࡫ࡗࡧࡵࡷ࡮ࡵ࡮ࠨ∤"): framework.get(bstack1111ll_opy_ (u"ࠬࡹࡤ࡬ࡡࡹࡩࡷࡹࡩࡰࡰࠪ∥")),
    bstack1111ll_opy_ (u"࠭࡬ࡢࡰࡪࡹࡦ࡭ࡥࠨ∦"): bstack1111ll_opy_ (u"ࠧࡱࡻࡷ࡬ࡴࡴࠧ∧"),
    bstack1111ll_opy_ (u"ࠨࡶࡨࡷࡹࡌࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨ∨"): framework.get(bstack1111ll_opy_ (u"ࠩࡷࡩࡸࡺࡆࡳࡣࡰࡩࡼࡵࡲ࡬ࠩ∩"))
  }
def bstack1lll1llll111_opy_(bs_config):
  bstack1111ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࡔࡨࡸࡺࡸ࡮ࡴࠢࡷ࡬ࡪࠦࡴࡦࡵࡷࠤࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤࡩࡧࡴࡢࠢࡩࡳࡷࠦࡢࡶ࡫࡯ࡨࠥࡹࡴࡢࡴࡷ࠲ࠏࠦࠠࠣࠤࠥ∪")
  if not bs_config:
    return {}
  bstack1111ll1lll1_opy_ = bstack11l111ll_opy_(bs_config).bstack1111ll111ll_opy_(bs_config)
  return bstack1111ll1lll1_opy_
def bstack11ll1lll11_opy_(bs_config, framework):
  bstack111llll1l_opy_ = False
  bstack1l1111l1l_opy_ = False
  bstack1llll1111l1l_opy_ = False
  if bstack1111ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࠨ∫") in bs_config:
    bstack1llll1111l1l_opy_ = True
  elif bstack1111ll_opy_ (u"ࠬࡧࡰࡱࠩ∬") in bs_config:
    bstack111llll1l_opy_ = True
  else:
    bstack1l1111l1l_opy_ = True
  bstack1l1lllll1_opy_ = {
    bstack1111ll_opy_ (u"࠭࡯ࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠭∭"): bstack1ll1l111l1_opy_.bstack1lll1llllll1_opy_(bs_config, framework),
    bstack1111ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧ∮"): bstack1l1111lll_opy_.bstack1lll111l1l_opy_(bs_config),
    bstack1111ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࠧ∯"): bs_config.get(bstack1111ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࠨ∰"), False),
    bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯࡮ࡣࡷࡩࠬ∱"): bstack1l1111l1l_opy_,
    bstack1111ll_opy_ (u"ࠫࡦࡶࡰࡠࡣࡸࡸࡴࡳࡡࡵࡧࠪ∲"): bstack111llll1l_opy_,
    bstack1111ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡷࡨࡧ࡬ࡦࠩ∳"): bstack1llll1111l1l_opy_
  }
  return bstack1l1lllll1_opy_
@error_handler(class_method=False)
def bstack1lll1llll1l1_opy_(bs_config):
  try:
    bstack1llll111111l_opy_ = json.loads(os.getenv(bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡢࡅࡈࡉࡅࡔࡕࡌࡆࡎࡒࡉࡕ࡛ࡢࡇࡔࡔࡆࡊࡉࡘࡖࡆ࡚ࡉࡐࡐࡢ࡝ࡒࡒࠧ∴"), bstack1111ll_opy_ (u"ࠧࡼࡿࠪ∵")))
    bstack1llll111111l_opy_ = bstack1lll1lllll1l_opy_(bs_config, bstack1llll111111l_opy_)
    return {
        bstack1111ll_opy_ (u"ࠨࡵࡨࡸࡹ࡯࡮ࡨࡵࠪ∶"): bstack1llll111111l_opy_
    }
  except Exception as error:
    logger.error(bstack1111ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࡽࡨࡪ࡮ࡨࠤࡨࡸࡥࡢࡶ࡬ࡲ࡬ࠦࡧࡦࡶࡢࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡢࡷࡪࡺࡴࡪࡰࡪࡷࠥ࡬࡯ࡳࠢࡗࡩࡸࡺࡈࡶࡤ࠽ࠤࠥࢁࡽࠣ∷").format(str(error)))
    return {}
def bstack1lll1lllll1l_opy_(bs_config, bstack1llll111111l_opy_):
  if ((bstack1111ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡕࡦࡥࡱ࡫ࠧ∸") in bs_config or not bstack1l1l111l1_opy_(bs_config)) and bstack1l1111lll_opy_.bstack1lll111l1l_opy_(bs_config)):
    bstack1llll111111l_opy_[bstack1111ll_opy_ (u"ࠦ࡮ࡴࡣ࡭ࡷࡧࡩࡊࡴࡣࡰࡦࡨࡨࡊࡾࡴࡦࡰࡶ࡭ࡴࡴࠢ∹")] = True
  return bstack1llll111111l_opy_
def bstack1llll111llll_opy_(array, bstack1lll1lllll11_opy_, bstack1lll1llll11l_opy_):
  result = {}
  for o in array:
    key = o[bstack1lll1lllll11_opy_]
    result[key] = o[bstack1lll1llll11l_opy_]
  return result
def bstack1llll11ll1ll_opy_(bstack1lll1lll1_opy_=bstack1111ll_opy_ (u"ࠬ࠭∺")):
  bstack1llll1111l11_opy_ = bstack1l1111lll_opy_.on()
  bstack1llll1111111_opy_ = bstack1ll1l111l1_opy_.on()
  bstack1lll1llll1ll_opy_ = percy.bstack11l11l111l_opy_()
  if bstack1lll1llll1ll_opy_ and not bstack1llll1111111_opy_ and not bstack1llll1111l11_opy_:
    return bstack1lll1lll1_opy_ not in [bstack1111ll_opy_ (u"࠭ࡃࡃࡖࡖࡩࡸࡹࡩࡰࡰࡆࡶࡪࡧࡴࡦࡦࠪ∻"), bstack1111ll_opy_ (u"ࠧࡍࡱࡪࡇࡷ࡫ࡡࡵࡧࡧࠫ∼")]
  elif bstack1llll1111l11_opy_ and not bstack1llll1111111_opy_:
    return bstack1lll1lll1_opy_ not in [bstack1111ll_opy_ (u"ࠨࡊࡲࡳࡰࡘࡵ࡯ࡕࡷࡥࡷࡺࡥࡥࠩ∽"), bstack1111ll_opy_ (u"ࠩࡋࡳࡴࡱࡒࡶࡰࡉ࡭ࡳ࡯ࡳࡩࡧࡧࠫ∾"), bstack1111ll_opy_ (u"ࠪࡐࡴ࡭ࡃࡳࡧࡤࡸࡪࡪࠧ∿")]
  return bstack1llll1111l11_opy_ or bstack1llll1111111_opy_ or bstack1lll1llll1ll_opy_
@error_handler(class_method=False)
def bstack1llll11l1lll_opy_(bstack1lll1lll1_opy_, test=None):
  bstack1lll1lllllll_opy_ = bstack1l1111lll_opy_.on()
  if not bstack1lll1lllllll_opy_ or bstack1lll1lll1_opy_ not in [bstack1111ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡋ࡯࡮ࡪࡵ࡫ࡩࡩ࠭≀")] or test == None:
    return None
  return {
    bstack1111ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ≁"): bstack1lll1lllllll_opy_ and bstack1l1l11ll1l_opy_(threading.current_thread(), bstack1111ll_opy_ (u"࠭ࡡ࠲࠳ࡼࡔࡱࡧࡴࡧࡱࡵࡱࠬ≂"), None) == True and bstack1l1111lll_opy_.bstack1l1l1l11l1_opy_(test[bstack1111ll_opy_ (u"ࠧࡵࡣࡪࡷࠬ≃")])
  }
def bstack1llll11111ll_opy_(bs_config, framework):
  bstack111llll1l_opy_ = False
  bstack1l1111l1l_opy_ = False
  bstack1llll1111l1l_opy_ = False
  if bstack1111ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬ≄") in bs_config:
    bstack1llll1111l1l_opy_ = True
  elif bstack1111ll_opy_ (u"ࠩࡤࡴࡵ࠭≅") in bs_config:
    bstack111llll1l_opy_ = True
  else:
    bstack1l1111l1l_opy_ = True
  bstack1l1lllll1_opy_ = {
    bstack1111ll_opy_ (u"ࠪࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪ≆"): bstack1ll1l111l1_opy_.bstack1lll1llllll1_opy_(bs_config, framework),
    bstack1111ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫ≇"): bstack1l1111lll_opy_.bstack1llllll111_opy_(bs_config),
    bstack1111ll_opy_ (u"ࠬࡶࡥࡳࡥࡼࠫ≈"): bs_config.get(bstack1111ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࠬ≉"), False),
    bstack1111ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡦࠩ≊"): bstack1l1111l1l_opy_,
    bstack1111ll_opy_ (u"ࠨࡣࡳࡴࡤࡧࡵࡵࡱࡰࡥࡹ࡫ࠧ≋"): bstack111llll1l_opy_,
    bstack1111ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡴࡥࡤࡰࡪ࠭≌"): bstack1llll1111l1l_opy_
  }
  return bstack1l1lllll1_opy_