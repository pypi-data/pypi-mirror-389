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
import os
import threading
from bstack_utils.config import Config
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.helper import bstack111lll111l1_opy_, bstack111l1l1l_opy_, bstack1l1l11ll1l_opy_, bstack1llllllll1_opy_, \
    bstack11l1111l1ll_opy_
from bstack_utils.measure import measure
def bstack1l1l111111_opy_(bstack1lllll111l1l_opy_):
    for driver in bstack1lllll111l1l_opy_:
        try:
            driver.quit()
        except Exception as e:
            pass
@measure(event_name=EVENTS.bstack1l1111l111_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
def bstack1l1ll1l1_opy_(driver, status, reason=bstack1111ll_opy_ (u"ࠩࠪ⁍")):
    bstack1l1l11ll11_opy_ = Config.bstack111l11ll1_opy_()
    if bstack1l1l11ll11_opy_.bstack11111ll111_opy_():
        return
    bstack11ll11111_opy_ = bstack1ll1l11l11_opy_(bstack1111ll_opy_ (u"ࠪࡷࡪࡺࡓࡦࡵࡶ࡭ࡴࡴࡓࡵࡣࡷࡹࡸ࠭⁎"), bstack1111ll_opy_ (u"ࠫࠬ⁏"), status, reason, bstack1111ll_opy_ (u"ࠬ࠭⁐"), bstack1111ll_opy_ (u"࠭ࠧ⁑"))
    driver.execute_script(bstack11ll11111_opy_)
@measure(event_name=EVENTS.bstack1l1111l111_opy_, stage=STAGE.bstack11ll1ll1ll_opy_)
def bstack1l11ll1l11_opy_(page, status, reason=bstack1111ll_opy_ (u"ࠧࠨ⁒")):
    try:
        if page is None:
            return
        bstack1l1l11ll11_opy_ = Config.bstack111l11ll1_opy_()
        if bstack1l1l11ll11_opy_.bstack11111ll111_opy_():
            return
        bstack11ll11111_opy_ = bstack1ll1l11l11_opy_(bstack1111ll_opy_ (u"ࠨࡵࡨࡸࡘ࡫ࡳࡴ࡫ࡲࡲࡘࡺࡡࡵࡷࡶࠫ⁓"), bstack1111ll_opy_ (u"ࠩࠪ⁔"), status, reason, bstack1111ll_opy_ (u"ࠪࠫ⁕"), bstack1111ll_opy_ (u"ࠫࠬ⁖"))
        page.evaluate(bstack1111ll_opy_ (u"ࠧࡥࠠ࠾ࡀࠣࡿࢂࠨ⁗"), bstack11ll11111_opy_)
    except Exception as e:
        print(bstack1111ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡹࡥࡵࡶ࡬ࡲ࡬ࠦࡳࡦࡵࡶ࡭ࡴࡴࠠࡴࡶࡤࡸࡺࡹࠠࡧࡱࡵࠤࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࠡࡽࢀࠦ⁘"), e)
def bstack1ll1l11l11_opy_(type, name, status, reason, bstack1l1lll1l1l_opy_, bstack11ll111ll_opy_):
    bstack1lll1111ll_opy_ = {
        bstack1111ll_opy_ (u"ࠧࡢࡥࡷ࡭ࡴࡴࠧ⁙"): type,
        bstack1111ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫ⁚"): {}
    }
    if type == bstack1111ll_opy_ (u"ࠩࡤࡲࡳࡵࡴࡢࡶࡨࠫ⁛"):
        bstack1lll1111ll_opy_[bstack1111ll_opy_ (u"ࠪࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸ࠭⁜")][bstack1111ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪ⁝")] = bstack1l1lll1l1l_opy_
        bstack1lll1111ll_opy_[bstack1111ll_opy_ (u"ࠬࡧࡲࡨࡷࡰࡩࡳࡺࡳࠨ⁞")][bstack1111ll_opy_ (u"࠭ࡤࡢࡶࡤࠫ ")] = json.dumps(str(bstack11ll111ll_opy_))
    if type == bstack1111ll_opy_ (u"ࠧࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨ⁠"):
        bstack1lll1111ll_opy_[bstack1111ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫ⁡")][bstack1111ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ⁢")] = name
    if type == bstack1111ll_opy_ (u"ࠪࡷࡪࡺࡓࡦࡵࡶ࡭ࡴࡴࡓࡵࡣࡷࡹࡸ࠭⁣"):
        bstack1lll1111ll_opy_[bstack1111ll_opy_ (u"ࠫࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠧ⁤")][bstack1111ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬ⁥")] = status
        if status == bstack1111ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡩࡩ࠭⁦") and str(reason) != bstack1111ll_opy_ (u"ࠢࠣ⁧"):
            bstack1lll1111ll_opy_[bstack1111ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫ⁨")][bstack1111ll_opy_ (u"ࠩࡵࡩࡦࡹ࡯࡯ࠩ⁩")] = json.dumps(str(reason))
    bstack11ll1l1l11_opy_ = bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࡽࠨ⁪").format(json.dumps(bstack1lll1111ll_opy_))
    return bstack11ll1l1l11_opy_
def bstack11l111lll_opy_(url, config, logger, bstack11llll1l_opy_=False):
    hostname = bstack111l1l1l_opy_(url)
    is_private = bstack1llllllll1_opy_(hostname)
    try:
        if is_private or bstack11llll1l_opy_:
            file_path = bstack111lll111l1_opy_(bstack1111ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫ⁫"), bstack1111ll_opy_ (u"ࠬ࠴ࡢࡴࡶࡤࡧࡰ࠳ࡣࡰࡰࡩ࡭࡬࠴ࡪࡴࡱࡱࠫ⁬"), logger)
            if os.environ.get(bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡒࡏࡄࡃࡏࡣࡓࡕࡔࡠࡕࡈࡘࡤࡋࡒࡓࡑࡕࠫ⁭")) and eval(
                    os.environ.get(bstack1111ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡌࡐࡅࡄࡐࡤࡔࡏࡕࡡࡖࡉ࡙ࡥࡅࡓࡔࡒࡖࠬ⁮"))):
                return
            if (bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬ⁯") in config and not config[bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡍࡱࡦࡥࡱ࠭⁰")]):
                os.environ[bstack1111ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡏࡓࡈࡇࡌࡠࡐࡒࡘࡤ࡙ࡅࡕࡡࡈࡖࡗࡕࡒࠨⁱ")] = str(True)
                bstack1lllll1111ll_opy_ = {bstack1111ll_opy_ (u"ࠫ࡭ࡵࡳࡵࡰࡤࡱࡪ࠭⁲"): hostname}
                bstack11l1111l1ll_opy_(bstack1111ll_opy_ (u"ࠬ࠴ࡢࡴࡶࡤࡧࡰ࠳ࡣࡰࡰࡩ࡭࡬࠴ࡪࡴࡱࡱࠫ⁳"), bstack1111ll_opy_ (u"࠭࡮ࡶࡦࡪࡩࡤࡲ࡯ࡤࡣ࡯ࠫ⁴"), bstack1lllll1111ll_opy_, logger)
    except Exception as e:
        pass
def bstack1l1llll111_opy_(caps, bstack1lllll1111l1_opy_):
    if bstack1111ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨ⁵") in caps:
        caps[bstack1111ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫࠻ࡱࡳࡸ࡮ࡵ࡮ࡴࠩ⁶")][bstack1111ll_opy_ (u"ࠩ࡯ࡳࡨࡧ࡬ࠨ⁷")] = True
        if bstack1lllll1111l1_opy_:
            caps[bstack1111ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭࠽ࡳࡵࡺࡩࡰࡰࡶࠫ⁸")][bstack1111ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭⁹")] = bstack1lllll1111l1_opy_
    else:
        caps[bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡱࡵࡣࡢ࡮ࠪ⁺")] = True
        if bstack1lllll1111l1_opy_:
            caps[bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡲ࡯ࡤࡣ࡯ࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧ⁻")] = bstack1lllll1111l1_opy_
def bstack1lllll1lllll_opy_(bstack111l1111ll_opy_):
    bstack1lllll111l11_opy_ = bstack1l1l11ll1l_opy_(threading.current_thread(), bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡘࡺࡡࡵࡷࡶࠫ⁼"), bstack1111ll_opy_ (u"ࠨࠩ⁽"))
    if bstack1lllll111l11_opy_ == bstack1111ll_opy_ (u"ࠩࠪ⁾") or bstack1lllll111l11_opy_ == bstack1111ll_opy_ (u"ࠪࡷࡰ࡯ࡰࡱࡧࡧࠫⁿ"):
        threading.current_thread().testStatus = bstack111l1111ll_opy_
    else:
        if bstack111l1111ll_opy_ == bstack1111ll_opy_ (u"ࠫ࡫ࡧࡩ࡭ࡧࡧࠫ₀"):
            threading.current_thread().testStatus = bstack111l1111ll_opy_