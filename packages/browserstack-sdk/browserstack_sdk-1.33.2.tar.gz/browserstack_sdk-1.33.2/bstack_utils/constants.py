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
import re
from enum import Enum
bstack1lllllll1l_opy_ = {
  bstack1111ll_opy_ (u"ࠫࡺࡹࡥࡳࡐࡤࡱࡪ࠭ឹ"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡺࡹࡥࡳࠩឺ"),
  bstack1111ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸࡑࡥࡺࠩុ"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴࡫ࡦࡻࠪូ"),
  bstack1111ll_opy_ (u"ࠨࡱࡶ࡚ࡪࡸࡳࡪࡱࡱࠫួ"): bstack1111ll_opy_ (u"ࠩࡲࡷࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭ើ"),
  bstack1111ll_opy_ (u"ࠪࡹࡸ࡫ࡗ࠴ࡅࠪឿ"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡹࡸ࡫࡟ࡸ࠵ࡦࠫៀ"),
  bstack1111ll_opy_ (u"ࠬࡶࡲࡰ࡬ࡨࡧࡹࡔࡡ࡮ࡧࠪេ"): bstack1111ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࠧែ"),
  bstack1111ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪៃ"): bstack1111ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࠧោ"),
  bstack1111ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧៅ"): bstack1111ll_opy_ (u"ࠪࡲࡦࡳࡥࠨំ"),
  bstack1111ll_opy_ (u"ࠫࡩ࡫ࡢࡶࡩࠪះ"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡩ࡫ࡢࡶࡩࠪៈ"),
  bstack1111ll_opy_ (u"࠭ࡣࡰࡰࡶࡳࡱ࡫ࡌࡰࡩࡶࠫ៉"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡣࡰࡰࡶࡳࡱ࡫ࠧ៊"),
  bstack1111ll_opy_ (u"ࠨࡰࡨࡸࡼࡵࡲ࡬ࡎࡲ࡫ࡸ࠭់"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡰࡨࡸࡼࡵࡲ࡬ࡎࡲ࡫ࡸ࠭៌"),
  bstack1111ll_opy_ (u"ࠪࡥࡵࡶࡩࡶ࡯ࡏࡳ࡬ࡹࠧ៍"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡵࡶࡩࡶ࡯ࡏࡳ࡬ࡹࠧ៎"),
  bstack1111ll_opy_ (u"ࠬࡼࡩࡥࡧࡲࠫ៏"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡼࡩࡥࡧࡲࠫ័"),
  bstack1111ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡎࡲ࡫ࡸ࠭៑"): bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡎࡲ࡫ࡸ្࠭"),
  bstack1111ll_opy_ (u"ࠩࡷࡩࡱ࡫࡭ࡦࡶࡵࡽࡑࡵࡧࡴࠩ៓"): bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡷࡩࡱ࡫࡭ࡦࡶࡵࡽࡑࡵࡧࡴࠩ។"),
  bstack1111ll_opy_ (u"ࠫ࡬࡫࡯ࡍࡱࡦࡥࡹ࡯࡯࡯ࠩ៕"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲࡬࡫࡯ࡍࡱࡦࡥࡹ࡯࡯࡯ࠩ៖"),
  bstack1111ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡾࡴࡴࡥࠨៗ"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡴࡪ࡯ࡨࡾࡴࡴࡥࠨ៘"),
  bstack1111ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯࡙ࡩࡷࡹࡩࡰࡰࠪ៙"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡵࡨࡰࡪࡴࡩࡶ࡯ࡢࡺࡪࡸࡳࡪࡱࡱࠫ៚"),
  bstack1111ll_opy_ (u"ࠪࡱࡦࡹ࡫ࡄࡱࡰࡱࡦࡴࡤࡴࠩ៛"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡱࡦࡹ࡫ࡄࡱࡰࡱࡦࡴࡤࡴࠩៜ"),
  bstack1111ll_opy_ (u"ࠬ࡯ࡤ࡭ࡧࡗ࡭ࡲ࡫࡯ࡶࡶࠪ៝"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳࡯ࡤ࡭ࡧࡗ࡭ࡲ࡫࡯ࡶࡶࠪ៞"),
  bstack1111ll_opy_ (u"ࠧ࡮ࡣࡶ࡯ࡇࡧࡳࡪࡥࡄࡹࡹ࡮ࠧ៟"): bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮࡮ࡣࡶ࡯ࡇࡧࡳࡪࡥࡄࡹࡹ࡮ࠧ០"),
  bstack1111ll_opy_ (u"ࠩࡶࡩࡳࡪࡋࡦࡻࡶࠫ១"): bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡶࡩࡳࡪࡋࡦࡻࡶࠫ២"),
  bstack1111ll_opy_ (u"ࠫࡦࡻࡴࡰ࡙ࡤ࡭ࡹ࠭៣"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡻࡴࡰ࡙ࡤ࡭ࡹ࠭៤"),
  bstack1111ll_opy_ (u"࠭ࡨࡰࡵࡷࡷࠬ៥"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡨࡰࡵࡷࡷࠬ៦"),
  bstack1111ll_opy_ (u"ࠨࡤࡩࡧࡦࡩࡨࡦࠩ៧"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡩࡧࡦࡩࡨࡦࠩ៨"),
  bstack1111ll_opy_ (u"ࠪࡻࡸࡒ࡯ࡤࡣ࡯ࡗࡺࡶࡰࡰࡴࡷࠫ៩"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡻࡸࡒ࡯ࡤࡣ࡯ࡗࡺࡶࡰࡰࡴࡷࠫ៪"),
  bstack1111ll_opy_ (u"ࠬࡪࡩࡴࡣࡥࡰࡪࡉ࡯ࡳࡵࡕࡩࡸࡺࡲࡪࡥࡷ࡭ࡴࡴࡳࠨ៫"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡪࡩࡴࡣࡥࡰࡪࡉ࡯ࡳࡵࡕࡩࡸࡺࡲࡪࡥࡷ࡭ࡴࡴࡳࠨ៬"),
  bstack1111ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࡎࡢ࡯ࡨࠫ៭"): bstack1111ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࠨ៮"),
  bstack1111ll_opy_ (u"ࠩࡵࡩࡦࡲࡍࡰࡤ࡬ࡰࡪ࠭៯"): bstack1111ll_opy_ (u"ࠪࡶࡪࡧ࡬ࡠ࡯ࡲࡦ࡮ࡲࡥࠨ៰"),
  bstack1111ll_opy_ (u"ࠫࡦࡶࡰࡪࡷࡰ࡚ࡪࡸࡳࡪࡱࡱࠫ៱"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡶࡰࡪࡷࡰࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬ៲"),
  bstack1111ll_opy_ (u"࠭ࡣࡶࡵࡷࡳࡲࡔࡥࡵࡹࡲࡶࡰ࠭៳"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡣࡶࡵࡷࡳࡲࡔࡥࡵࡹࡲࡶࡰ࠭៴"),
  bstack1111ll_opy_ (u"ࠨࡰࡨࡸࡼࡵࡲ࡬ࡒࡵࡳ࡫࡯࡬ࡦࠩ៵"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡰࡨࡸࡼࡵࡲ࡬ࡒࡵࡳ࡫࡯࡬ࡦࠩ៶"),
  bstack1111ll_opy_ (u"ࠪࡥࡨࡩࡥࡱࡶࡌࡲࡸ࡫ࡣࡶࡴࡨࡇࡪࡸࡴࡴࠩ៷"): bstack1111ll_opy_ (u"ࠫࡦࡩࡣࡦࡲࡷࡗࡸࡲࡃࡦࡴࡷࡷࠬ៸"),
  bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧ៹"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧ៺"),
  bstack1111ll_opy_ (u"ࠧࡴࡱࡸࡶࡨ࡫ࠧ៻"): bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡴࡱࡸࡶࡨ࡫ࠧ៼"),
  bstack1111ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫ៽"): bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫ៾"),
  bstack1111ll_opy_ (u"ࠫ࡭ࡵࡳࡵࡐࡤࡱࡪ࠭៿"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲࡭ࡵࡳࡵࡐࡤࡱࡪ࠭᠀"),
  bstack1111ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪ࡙ࡩ࡮ࠩ᠁"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡥ࡯ࡣࡥࡰࡪ࡙ࡩ࡮ࠩ᠂"),
  bstack1111ll_opy_ (u"ࠨࡵ࡬ࡱࡔࡶࡴࡪࡱࡱࡷࠬ᠃"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡵ࡬ࡱࡔࡶࡴࡪࡱࡱࡷࠬ᠄"),
  bstack1111ll_opy_ (u"ࠪࡹࡵࡲ࡯ࡢࡦࡐࡩࡩ࡯ࡡࠨ᠅"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡹࡵࡲ࡯ࡢࡦࡐࡩࡩ࡯ࡡࠨ᠆"),
  bstack1111ll_opy_ (u"ࠬࡺࡥࡴࡶ࡫ࡹࡧࡈࡵࡪ࡮ࡧ࡙ࡺ࡯ࡤࠨ᠇"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡺࡥࡴࡶ࡫ࡹࡧࡈࡵࡪ࡮ࡧ࡙ࡺ࡯ࡤࠨ᠈"),
  bstack1111ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡖࡲࡰࡦࡸࡧࡹࡓࡡࡱࠩ᠉"): bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡣࡷ࡬ࡰࡩࡖࡲࡰࡦࡸࡧࡹࡓࡡࡱࠩ᠊")
}
bstack11l1l11llll_opy_ = [
  bstack1111ll_opy_ (u"ࠩࡲࡷࠬ᠋"),
  bstack1111ll_opy_ (u"ࠪࡳࡸ࡜ࡥࡳࡵ࡬ࡳࡳ࠭᠌"),
  bstack1111ll_opy_ (u"ࠫࡸ࡫࡬ࡦࡰ࡬ࡹࡲ࡜ࡥࡳࡵ࡬ࡳࡳ࠭᠍"),
  bstack1111ll_opy_ (u"ࠬࡹࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠪ᠎"),
  bstack1111ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪࡔࡡ࡮ࡧࠪ᠏"),
  bstack1111ll_opy_ (u"ࠧࡳࡧࡤࡰࡒࡵࡢࡪ࡮ࡨࠫ᠐"),
  bstack1111ll_opy_ (u"ࠨࡣࡳࡴ࡮ࡻ࡭ࡗࡧࡵࡷ࡮ࡵ࡮ࠨ᠑"),
]
bstack1ll1l11l_opy_ = {
  bstack1111ll_opy_ (u"ࠩࡸࡷࡪࡸࡎࡢ࡯ࡨࠫ᠒"): [bstack1111ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡘࡗࡊࡘࡎࡂࡏࡈࠫ᠓"), bstack1111ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢ࡙ࡘࡋࡒࡠࡐࡄࡑࡊ࠭᠔")],
  bstack1111ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨ᠕"): bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡇࡃࡄࡇࡖࡗࡤࡑࡅ࡚ࠩ᠖"),
  bstack1111ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪ᠗"): bstack1111ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡗࡌࡐࡉࡥࡎࡂࡏࡈࠫ᠘"),
  bstack1111ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧ᠙"): bstack1111ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓࡖࡔࡐࡅࡄࡖࡢࡒࡆࡓࡅࠨ᠚"),
  bstack1111ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭᠛"): bstack1111ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇ࡛ࡉࡍࡆࡢࡍࡉࡋࡎࡕࡋࡉࡍࡊࡘࠧ᠜"),
  bstack1111ll_opy_ (u"࠭ࡰࡢࡴࡤࡰࡱ࡫࡬ࡴࡒࡨࡶࡕࡲࡡࡵࡨࡲࡶࡲ࠭᠝"): bstack1111ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡂࡔࡄࡐࡑࡋࡌࡔࡡࡓࡉࡗࡥࡐࡍࡃࡗࡊࡔࡘࡍࠨ᠞"),
  bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬ᠟"): bstack1111ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡎࡒࡇࡆࡒࠧᠠ"),
  bstack1111ll_opy_ (u"ࠪࡶࡪࡸࡵ࡯ࡖࡨࡷࡹࡹࠧᠡ"): bstack1111ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡖࡊࡘࡕࡏࡡࡗࡉࡘ࡚ࡓࠨᠢ"),
  bstack1111ll_opy_ (u"ࠬࡧࡰࡱࠩᠣ"): [bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡇࡐࡑࡡࡌࡈࠬᠤ"), bstack1111ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡁࡑࡒࠪᠥ")],
  bstack1111ll_opy_ (u"ࠨ࡮ࡲ࡫ࡑ࡫ࡶࡦ࡮ࠪᠦ"): bstack1111ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡕࡇࡏࡤࡒࡏࡈࡎࡈ࡚ࡊࡒࠧᠧ"),
  bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࠧᠨ"): bstack1111ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧᠩ"),
  bstack1111ll_opy_ (u"ࠬࡺࡥࡴࡶࡒࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࠩᠪ"): [bstack1111ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡢࡓࡇ࡙ࡅࡓࡘࡄࡆࡎࡒࡉࡕ࡛ࠪᠫ"), bstack1111ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡗࡋࡐࡐࡔࡗࡍࡓࡍࠧᠬ")],
  bstack1111ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬᠭ"): bstack1111ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡘࡖࡇࡕࡓࡄࡃࡏࡉࠬᠮ"),
  bstack1111ll_opy_ (u"ࠪࡷࡲࡧࡲࡵࡕࡨࡰࡪࡩࡴࡪࡱࡱࡊࡪࡧࡴࡶࡴࡨࡆࡷࡧ࡮ࡤࡪࡨࡷࡊࡔࡖࠨᠯ"): bstack1111ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡓࡗࡉࡈࡆࡕࡗࡖࡆ࡚ࡉࡐࡐࡢࡗࡒࡇࡒࡕࡡࡖࡉࡑࡋࡃࡕࡋࡒࡒࡤࡌࡅࡂࡖࡘࡖࡊࡥࡂࡓࡃࡑࡇࡍࡋࡓࠨᠰ")
}
bstack11llllll1_opy_ = {
  bstack1111ll_opy_ (u"ࠬࡻࡳࡦࡴࡑࡥࡲ࡫ࠧᠱ"): [bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡻࡳࡦࡴࡢࡲࡦࡳࡥࠨᠲ"), bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡵࡴࡧࡵࡒࡦࡳࡥࠨᠳ")],
  bstack1111ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫᠴ"): [bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡣࡦࡧࡪࡹࡳࡠ࡭ࡨࡽࠬᠵ"), bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬᠶ")],
  bstack1111ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧᠷ"): bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧᠸ"),
  bstack1111ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫᠹ"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫᠺ"),
  bstack1111ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪᠻ"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪᠼ"),
  bstack1111ll_opy_ (u"ࠪࡴࡦࡸࡡ࡭࡮ࡨࡰࡸࡖࡥࡳࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪᠽ"): [bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡴࡵࡶࠧᠾ"), bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡵࡧࡲࡢ࡮࡯ࡩࡱࡹࡐࡦࡴࡓࡰࡦࡺࡦࡰࡴࡰࠫᠿ")],
  bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪᡀ"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴࡬ࡰࡥࡤࡰࠬᡁ"),
  bstack1111ll_opy_ (u"ࠨࡴࡨࡶࡺࡴࡔࡦࡵࡷࡷࠬᡂ"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡴࡨࡶࡺࡴࡔࡦࡵࡷࡷࠬᡃ"),
  bstack1111ll_opy_ (u"ࠪࡥࡵࡶࠧᡄ"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡵࡶࠧᡅ"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡨࡎࡨࡺࡪࡲࠧᡆ"): bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡲ࡯ࡨࡎࡨࡺࡪࡲࠧᡇ"),
  bstack1111ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᡈ"): bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᡉ"),
  bstack1111ll_opy_ (u"ࠤࡶࡱࡦࡸࡴࡔࡧ࡯ࡩࡨࡺࡩࡰࡰࡉࡩࡦࡺࡵࡳࡧࡅࡶࡦࡴࡣࡩࡧࡶࡇࡑࡏࠢᡊ"): bstack1111ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡷࡩࡸࡺࡏࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳ࠴ࡳ࡮ࡣࡵࡸࡘ࡫࡬ࡦࡥࡷ࡭ࡴࡴࡆࡦࡣࡷࡹࡷ࡫ࡂࡳࡣࡱࡧ࡭࡫ࡳࠣᡋ"),
}
bstack11ll1l1l1l_opy_ = {
  bstack1111ll_opy_ (u"ࠫࡴࡹࡖࡦࡴࡶ࡭ࡴࡴࠧᡌ"): bstack1111ll_opy_ (u"ࠬࡵࡳࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᡍ"),
  bstack1111ll_opy_ (u"࠭ࡳࡦ࡮ࡨࡲ࡮ࡻ࡭ࡗࡧࡵࡷ࡮ࡵ࡮ࠨᡎ"): [bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡳࡦ࡮ࡨࡲ࡮ࡻ࡭ࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᡏ"), bstack1111ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯ࡢࡺࡪࡸࡳࡪࡱࡱࠫᡐ")],
  bstack1111ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧᡑ"): bstack1111ll_opy_ (u"ࠪࡲࡦࡳࡥࠨᡒ"),
  bstack1111ll_opy_ (u"ࠫࡩ࡫ࡶࡪࡥࡨࡒࡦࡳࡥࠨᡓ"): bstack1111ll_opy_ (u"ࠬࡪࡥࡷ࡫ࡦࡩࠬᡔ"),
  bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡎࡢ࡯ࡨࠫᡕ"): [bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࠨᡖ"), bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡡࡱࡥࡲ࡫ࠧᡗ")],
  bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪᡘ"): bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬᡙ"),
  bstack1111ll_opy_ (u"ࠫࡷ࡫ࡡ࡭ࡏࡲࡦ࡮ࡲࡥࠨᡚ"): bstack1111ll_opy_ (u"ࠬࡸࡥࡢ࡮ࡢࡱࡴࡨࡩ࡭ࡧࠪᡛ"),
  bstack1111ll_opy_ (u"࠭ࡡࡱࡲ࡬ࡹࡲ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᡜ"): [bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡡࡱࡲ࡬ࡹࡲࡥࡶࡦࡴࡶ࡭ࡴࡴࠧᡝ"), bstack1111ll_opy_ (u"ࠨࡣࡳࡴ࡮ࡻ࡭ࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᡞ")],
  bstack1111ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡰࡵࡋࡱࡷࡪࡩࡵࡳࡧࡆࡩࡷࡺࡳࠨᡟ"): [bstack1111ll_opy_ (u"ࠪࡥࡨࡩࡥࡱࡶࡖࡷࡱࡉࡥࡳࡶࡶࠫᡠ"), bstack1111ll_opy_ (u"ࠫࡦࡩࡣࡦࡲࡷࡗࡸࡲࡃࡦࡴࡷࠫᡡ")]
}
bstack1lll1l1ll1_opy_ = [
  bstack1111ll_opy_ (u"ࠬࡧࡣࡤࡧࡳࡸࡎࡴࡳࡦࡥࡸࡶࡪࡉࡥࡳࡶࡶࠫᡢ"),
  bstack1111ll_opy_ (u"࠭ࡰࡢࡩࡨࡐࡴࡧࡤࡔࡶࡵࡥࡹ࡫ࡧࡺࠩᡣ"),
  bstack1111ll_opy_ (u"ࠧࡱࡴࡲࡼࡾ࠭ᡤ"),
  bstack1111ll_opy_ (u"ࠨࡵࡨࡸ࡜࡯࡮ࡥࡱࡺࡖࡪࡩࡴࠨᡥ"),
  bstack1111ll_opy_ (u"ࠩࡷ࡭ࡲ࡫࡯ࡶࡶࡶࠫᡦ"),
  bstack1111ll_opy_ (u"ࠪࡷࡹࡸࡩࡤࡶࡉ࡭ࡱ࡫ࡉ࡯ࡶࡨࡶࡦࡩࡴࡢࡤ࡬ࡰ࡮ࡺࡹࠨᡧ"),
  bstack1111ll_opy_ (u"ࠫࡺࡴࡨࡢࡰࡧࡰࡪࡪࡐࡳࡱࡰࡴࡹࡈࡥࡩࡣࡹ࡭ࡴࡸࠧᡨ"),
  bstack1111ll_opy_ (u"ࠬ࡭࡯ࡰࡩ࠽ࡧ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᡩ"),
  bstack1111ll_opy_ (u"࠭࡭ࡰࡼ࠽ࡪ࡮ࡸࡥࡧࡱࡻࡓࡵࡺࡩࡰࡰࡶࠫᡪ"),
  bstack1111ll_opy_ (u"ࠧ࡮ࡵ࠽ࡩࡩ࡭ࡥࡐࡲࡷ࡭ࡴࡴࡳࠨᡫ"),
  bstack1111ll_opy_ (u"ࠨࡵࡨ࠾࡮࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᡬ"),
  bstack1111ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪ࠰ࡲࡴࡹ࡯࡯࡯ࡵࠪᡭ"),
]
bstack11lllll1l_opy_ = [
  bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࠧᡮ"),
  bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡘࡺࡡࡤ࡭ࡏࡳࡨࡧ࡬ࡐࡲࡷ࡭ࡴࡴࡳࠨᡯ"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡓࡵࡺࡩࡰࡰࡶࠫᡰ"),
  bstack1111ll_opy_ (u"࠭ࡰࡢࡴࡤࡰࡱ࡫࡬ࡴࡒࡨࡶࡕࡲࡡࡵࡨࡲࡶࡲ࠭ᡱ"),
  bstack1111ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪᡲ"),
  bstack1111ll_opy_ (u"ࠨ࡮ࡲ࡫ࡑ࡫ࡶࡦ࡮ࠪᡳ"),
  bstack1111ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡐࡳࡱࡻࡽࠬᡴ"),
  bstack1111ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴࡒࡵࡳࡽࡿࠧᡵ"),
  bstack1111ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱࠧᡶ"),
  bstack1111ll_opy_ (u"ࠬࡺࡥࡴࡶࡆࡳࡳࡺࡥࡹࡶࡒࡴࡹ࡯࡯࡯ࡵࠪᡷ"),
  bstack1111ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪᡸ"),
  bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡗ࡫ࡰࡰࡴࡷ࡭ࡳ࡭ࠧ᡹"),
  bstack1111ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭ࡗࡣࡵ࡭ࡦࡨ࡬ࡦࡵࠪ᡺"),
  bstack1111ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡖࡤ࡫ࠬ᡻"),
  bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࠧ᡼"),
  bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳ࠭᡽"),
  bstack1111ll_opy_ (u"ࠬࡸࡥࡳࡷࡱࡘࡪࡹࡴࡴࠩ᡾"),
  bstack1111ll_opy_ (u"࠭ࡃࡖࡕࡗࡓࡒࡥࡔࡂࡉࡢ࠵ࠬ᡿"),
  bstack1111ll_opy_ (u"ࠧࡄࡗࡖࡘࡔࡓ࡟ࡕࡃࡊࡣ࠷࠭ᢀ"),
  bstack1111ll_opy_ (u"ࠨࡅࡘࡗ࡙ࡕࡍࡠࡖࡄࡋࡤ࠹ࠧᢁ"),
  bstack1111ll_opy_ (u"ࠩࡆ࡙ࡘ࡚ࡏࡎࡡࡗࡅࡌࡥ࠴ࠨᢂ"),
  bstack1111ll_opy_ (u"ࠪࡇ࡚࡙ࡔࡐࡏࡢࡘࡆࡍ࡟࠶ࠩᢃ"),
  bstack1111ll_opy_ (u"ࠫࡈ࡛ࡓࡕࡑࡐࡣ࡙ࡇࡇࡠ࠸ࠪᢄ"),
  bstack1111ll_opy_ (u"ࠬࡉࡕࡔࡖࡒࡑࡤ࡚ࡁࡈࡡ࠺ࠫᢅ"),
  bstack1111ll_opy_ (u"࠭ࡃࡖࡕࡗࡓࡒࡥࡔࡂࡉࡢ࠼ࠬᢆ"),
  bstack1111ll_opy_ (u"ࠧࡄࡗࡖࡘࡔࡓ࡟ࡕࡃࡊࡣ࠾࠭ᢇ"),
  bstack1111ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࠧᢈ"),
  bstack1111ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࡐࡲࡷ࡭ࡴࡴࡳࠨᢉ"),
  bstack1111ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࡅࡤࡴࡹࡻࡲࡦࡏࡲࡨࡪ࠭ᢊ"),
  bstack1111ll_opy_ (u"ࠫࡩ࡯ࡳࡢࡤ࡯ࡩࡆࡻࡴࡰࡅࡤࡴࡹࡻࡲࡦࡎࡲ࡫ࡸ࠭ᢋ"),
  bstack1111ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࠩᢌ"),
  bstack1111ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᢍ"),
  bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡔࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࡓࡵࡺࡩࡰࡰࡶࠫᢎ"),
  bstack1111ll_opy_ (u"ࠨࡪࡸࡦࡗ࡫ࡧࡪࡱࡱࠫᢏ")
]
bstack11l1ll11l1l_opy_ = [
  bstack1111ll_opy_ (u"ࠩࡸࡴࡱࡵࡡࡥࡏࡨࡨ࡮ࡧࠧᢐ"),
  bstack1111ll_opy_ (u"ࠪࡹࡸ࡫ࡲࡏࡣࡰࡩࠬᢑ"),
  bstack1111ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶࡏࡪࡿࠧᢒ"),
  bstack1111ll_opy_ (u"ࠬࡹࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠪᢓ"),
  bstack1111ll_opy_ (u"࠭ࡴࡦࡵࡷࡔࡷ࡯࡯ࡳ࡫ࡷࡽࠬᢔ"),
  bstack1111ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪᢕ"),
  bstack1111ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡔࡢࡩࠪᢖ"),
  bstack1111ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧᢗ"),
  bstack1111ll_opy_ (u"ࠪࡷࡪࡲࡥ࡯࡫ࡸࡱ࡛࡫ࡲࡴ࡫ࡲࡲࠬᢘ"),
  bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦࠩᢙ"),
  bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᢚ"),
  bstack1111ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࠬᢛ"),
  bstack1111ll_opy_ (u"ࠧࡰࡵࠪᢜ"),
  bstack1111ll_opy_ (u"ࠨࡱࡶ࡚ࡪࡸࡳࡪࡱࡱࠫᢝ"),
  bstack1111ll_opy_ (u"ࠩ࡫ࡳࡸࡺࡳࠨᢞ"),
  bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯ࡘࡣ࡬ࡸࠬᢟ"),
  bstack1111ll_opy_ (u"ࠫࡷ࡫ࡧࡪࡱࡱࠫᢠ"),
  bstack1111ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡽࡳࡳ࡫ࠧᢡ"),
  bstack1111ll_opy_ (u"࠭࡭ࡢࡥ࡫࡭ࡳ࡫ࠧᢢ"),
  bstack1111ll_opy_ (u"ࠧࡳࡧࡶࡳࡱࡻࡴࡪࡱࡱࠫᢣ"),
  bstack1111ll_opy_ (u"ࠨ࡫ࡧࡰࡪ࡚ࡩ࡮ࡧࡲࡹࡹ࠭ᢤ"),
  bstack1111ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࡑࡵ࡭ࡪࡴࡴࡢࡶ࡬ࡳࡳ࠭ᢥ"),
  bstack1111ll_opy_ (u"ࠪࡺ࡮ࡪࡥࡰࠩᢦ"),
  bstack1111ll_opy_ (u"ࠫࡳࡵࡐࡢࡩࡨࡐࡴࡧࡤࡕ࡫ࡰࡩࡴࡻࡴࠨᢧ"),
  bstack1111ll_opy_ (u"ࠬࡨࡦࡤࡣࡦ࡬ࡪ࠭ᢨ"),
  bstack1111ll_opy_ (u"࠭ࡤࡦࡤࡸ࡫ᢩࠬ"),
  bstack1111ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳࡓࡤࡴࡨࡩࡳࡹࡨࡰࡶࡶࠫᢪ"),
  bstack1111ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭ࡔࡧࡱࡨࡐ࡫ࡹࡴࠩ᢫"),
  bstack1111ll_opy_ (u"ࠩࡵࡩࡦࡲࡍࡰࡤ࡬ࡰࡪ࠭᢬"),
  bstack1111ll_opy_ (u"ࠪࡲࡴࡖࡩࡱࡧ࡯࡭ࡳ࡫ࠧ᢭"),
  bstack1111ll_opy_ (u"ࠫࡨ࡮ࡥࡤ࡭ࡘࡖࡑ࠭᢮"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧ᢯"),
  bstack1111ll_opy_ (u"࠭ࡡࡤࡥࡨࡴࡹࡉ࡯ࡰ࡭࡬ࡩࡸ࠭ᢰ"),
  bstack1111ll_opy_ (u"ࠧࡤࡣࡳࡸࡺࡸࡥࡄࡴࡤࡷ࡭࠭ᢱ"),
  bstack1111ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࡏࡣࡰࡩࠬᢲ"),
  bstack1111ll_opy_ (u"ࠩࡤࡴࡵ࡯ࡵ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠩᢳ"),
  bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࡖࡦࡴࡶ࡭ࡴࡴࠧᢴ"),
  bstack1111ll_opy_ (u"ࠫࡳࡵࡂ࡭ࡣࡱ࡯ࡕࡵ࡬࡭࡫ࡱ࡫ࠬᢵ"),
  bstack1111ll_opy_ (u"ࠬࡳࡡࡴ࡭ࡖࡩࡳࡪࡋࡦࡻࡶࠫᢶ"),
  bstack1111ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪࡒ࡯ࡨࡵࠪᢷ"),
  bstack1111ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࡉࡥࠩᢸ"),
  bstack1111ll_opy_ (u"ࠨࡦࡨࡨ࡮ࡩࡡࡵࡧࡧࡈࡪࡼࡩࡤࡧࠪᢹ"),
  bstack1111ll_opy_ (u"ࠩ࡫ࡩࡦࡪࡥࡳࡒࡤࡶࡦࡳࡳࠨᢺ"),
  bstack1111ll_opy_ (u"ࠪࡴ࡭ࡵ࡮ࡦࡐࡸࡱࡧ࡫ࡲࠨᢻ"),
  bstack1111ll_opy_ (u"ࠫࡳ࡫ࡴࡸࡱࡵ࡯ࡑࡵࡧࡴࠩᢼ"),
  bstack1111ll_opy_ (u"ࠬࡴࡥࡵࡹࡲࡶࡰࡒ࡯ࡨࡵࡒࡴࡹ࡯࡯࡯ࡵࠪᢽ"),
  bstack1111ll_opy_ (u"࠭ࡣࡰࡰࡶࡳࡱ࡫ࡌࡰࡩࡶࠫᢾ"),
  bstack1111ll_opy_ (u"ࠧࡶࡵࡨ࡛࠸ࡉࠧᢿ"),
  bstack1111ll_opy_ (u"ࠨࡣࡳࡴ࡮ࡻ࡭ࡍࡱࡪࡷࠬᣀ"),
  bstack1111ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡄ࡬ࡳࡲ࡫ࡴࡳ࡫ࡦࠫᣁ"),
  bstack1111ll_opy_ (u"ࠪࡺ࡮ࡪࡥࡰࡘ࠵ࠫᣂ"),
  bstack1111ll_opy_ (u"ࠫࡲ࡯ࡤࡔࡧࡶࡷ࡮ࡵ࡮ࡊࡰࡶࡸࡦࡲ࡬ࡂࡲࡳࡷࠬᣃ"),
  bstack1111ll_opy_ (u"ࠬ࡫ࡳࡱࡴࡨࡷࡸࡵࡓࡦࡴࡹࡩࡷ࠭ᣄ"),
  bstack1111ll_opy_ (u"࠭ࡳࡦ࡮ࡨࡲ࡮ࡻ࡭ࡍࡱࡪࡷࠬᣅ"),
  bstack1111ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡅࡧࡴࠬᣆ"),
  bstack1111ll_opy_ (u"ࠨࡶࡨࡰࡪࡳࡥࡵࡴࡼࡐࡴ࡭ࡳࠨᣇ"),
  bstack1111ll_opy_ (u"ࠩࡶࡽࡳࡩࡔࡪ࡯ࡨ࡛࡮ࡺࡨࡏࡖࡓࠫᣈ"),
  bstack1111ll_opy_ (u"ࠪ࡫ࡪࡵࡌࡰࡥࡤࡸ࡮ࡵ࡮ࠨᣉ"),
  bstack1111ll_opy_ (u"ࠫ࡬ࡶࡳࡍࡱࡦࡥࡹ࡯࡯࡯ࠩᣊ"),
  bstack1111ll_opy_ (u"ࠬࡴࡥࡵࡹࡲࡶࡰࡖࡲࡰࡨ࡬ࡰࡪ࠭ᣋ"),
  bstack1111ll_opy_ (u"࠭ࡣࡶࡵࡷࡳࡲࡔࡥࡵࡹࡲࡶࡰ࠭ᣌ"),
  bstack1111ll_opy_ (u"ࠧࡧࡱࡵࡧࡪࡉࡨࡢࡰࡪࡩࡏࡧࡲࠨᣍ"),
  bstack1111ll_opy_ (u"ࠨࡺࡰࡷࡏࡧࡲࠨᣎ"),
  bstack1111ll_opy_ (u"ࠩࡻࡱࡽࡐࡡࡳࠩᣏ"),
  bstack1111ll_opy_ (u"ࠪࡱࡦࡹ࡫ࡄࡱࡰࡱࡦࡴࡤࡴࠩᣐ"),
  bstack1111ll_opy_ (u"ࠫࡲࡧࡳ࡬ࡄࡤࡷ࡮ࡩࡁࡶࡶ࡫ࠫᣑ"),
  bstack1111ll_opy_ (u"ࠬࡽࡳࡍࡱࡦࡥࡱ࡙ࡵࡱࡲࡲࡶࡹ࠭ᣒ"),
  bstack1111ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡃࡰࡴࡶࡖࡪࡹࡴࡳ࡫ࡦࡸ࡮ࡵ࡮ࡴࠩᣓ"),
  bstack1111ll_opy_ (u"ࠧࡢࡲࡳ࡚ࡪࡸࡳࡪࡱࡱࠫᣔ"),
  bstack1111ll_opy_ (u"ࠨࡣࡦࡧࡪࡶࡴࡊࡰࡶࡩࡨࡻࡲࡦࡅࡨࡶࡹࡹࠧᣕ"),
  bstack1111ll_opy_ (u"ࠩࡵࡩࡸ࡯ࡧ࡯ࡃࡳࡴࠬᣖ"),
  bstack1111ll_opy_ (u"ࠪࡨ࡮ࡹࡡࡣ࡮ࡨࡅࡳ࡯࡭ࡢࡶ࡬ࡳࡳࡹࠧᣗ"),
  bstack1111ll_opy_ (u"ࠫࡨࡧ࡮ࡢࡴࡼࠫᣘ"),
  bstack1111ll_opy_ (u"ࠬ࡬ࡩࡳࡧࡩࡳࡽ࠭ᣙ"),
  bstack1111ll_opy_ (u"࠭ࡣࡩࡴࡲࡱࡪ࠭ᣚ"),
  bstack1111ll_opy_ (u"ࠧࡪࡧࠪᣛ"),
  bstack1111ll_opy_ (u"ࠨࡧࡧ࡫ࡪ࠭ᣜ"),
  bstack1111ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪࠩᣝ"),
  bstack1111ll_opy_ (u"ࠪࡵࡺ࡫ࡵࡦࠩᣞ"),
  bstack1111ll_opy_ (u"ࠫ࡮ࡴࡴࡦࡴࡱࡥࡱ࠭ᣟ"),
  bstack1111ll_opy_ (u"ࠬࡧࡰࡱࡕࡷࡳࡷ࡫ࡃࡰࡰࡩ࡭࡬ࡻࡲࡢࡶ࡬ࡳࡳ࠭ᣠ"),
  bstack1111ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡉࡡ࡮ࡧࡵࡥࡎࡳࡡࡨࡧࡌࡲ࡯࡫ࡣࡵ࡫ࡲࡲࠬᣡ"),
  bstack1111ll_opy_ (u"ࠧ࡯ࡧࡷࡻࡴࡸ࡫ࡍࡱࡪࡷࡊࡾࡣ࡭ࡷࡧࡩࡍࡵࡳࡵࡵࠪᣢ"),
  bstack1111ll_opy_ (u"ࠨࡰࡨࡸࡼࡵࡲ࡬ࡎࡲ࡫ࡸࡏ࡮ࡤ࡮ࡸࡨࡪࡎ࡯ࡴࡶࡶࠫᣣ"),
  bstack1111ll_opy_ (u"ࠩࡸࡴࡩࡧࡴࡦࡃࡳࡴࡘ࡫ࡴࡵ࡫ࡱ࡫ࡸ࠭ᣤ"),
  bstack1111ll_opy_ (u"ࠪࡶࡪࡹࡥࡳࡸࡨࡈࡪࡼࡩࡤࡧࠪᣥ"),
  bstack1111ll_opy_ (u"ࠫࡸࡵࡵࡳࡥࡨࠫᣦ"),
  bstack1111ll_opy_ (u"ࠬࡹࡥ࡯ࡦࡎࡩࡾࡹࠧᣧ"),
  bstack1111ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡖࡡࡴࡵࡦࡳࡩ࡫ࠧᣨ"),
  bstack1111ll_opy_ (u"ࠧࡶࡲࡧࡥࡹ࡫ࡉࡰࡵࡇࡩࡻ࡯ࡣࡦࡕࡨࡸࡹ࡯࡮ࡨࡵࠪᣩ"),
  bstack1111ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡂࡷࡧ࡭ࡴࡏ࡮࡫ࡧࡦࡸ࡮ࡵ࡮ࠨᣪ"),
  bstack1111ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡃࡳࡴࡱ࡫ࡐࡢࡻࠪᣫ"),
  bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࠫᣬ"),
  bstack1111ll_opy_ (u"ࠫࡼࡪࡩࡰࡕࡨࡶࡻ࡯ࡣࡦࠩᣭ"),
  bstack1111ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᣮ"),
  bstack1111ll_opy_ (u"࠭ࡰࡳࡧࡹࡩࡳࡺࡃࡳࡱࡶࡷࡘ࡯ࡴࡦࡖࡵࡥࡨࡱࡩ࡯ࡩࠪᣯ"),
  bstack1111ll_opy_ (u"ࠧࡩ࡫ࡪ࡬ࡈࡵ࡮ࡵࡴࡤࡷࡹ࠭ᣰ"),
  bstack1111ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࡑࡴࡨࡪࡪࡸࡥ࡯ࡥࡨࡷࠬᣱ"),
  bstack1111ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡕ࡬ࡱࠬᣲ"),
  bstack1111ll_opy_ (u"ࠪࡷ࡮ࡳࡏࡱࡶ࡬ࡳࡳࡹࠧᣳ"),
  bstack1111ll_opy_ (u"ࠫࡷ࡫࡭ࡰࡸࡨࡍࡔ࡙ࡁࡱࡲࡖࡩࡹࡺࡩ࡯ࡩࡶࡐࡴࡩࡡ࡭࡫ࡽࡥࡹ࡯࡯࡯ࠩᣴ"),
  bstack1111ll_opy_ (u"ࠬ࡮࡯ࡴࡶࡑࡥࡲ࡫ࠧᣵ"),
  bstack1111ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ᣶"),
  bstack1111ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ᣷"),
  bstack1111ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡑࡥࡲ࡫ࠧ᣸"),
  bstack1111ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰ࡚ࡪࡸࡳࡪࡱࡱࠫ᣹"),
  bstack1111ll_opy_ (u"ࠪࡴࡦ࡭ࡥࡍࡱࡤࡨࡘࡺࡲࡢࡶࡨ࡫ࡾ࠭᣺"),
  bstack1111ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࠪ᣻"),
  bstack1111ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡲࡹࡹࡹࠧ᣼"),
  bstack1111ll_opy_ (u"࠭ࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࡒࡵࡳࡲࡶࡴࡃࡧ࡫ࡥࡻ࡯࡯ࡳࠩ᣽")
]
bstack11l11111l_opy_ = {
  bstack1111ll_opy_ (u"ࠧࡷࠩ᣾"): bstack1111ll_opy_ (u"ࠨࡸࠪ᣿"),
  bstack1111ll_opy_ (u"ࠩࡩࠫᤀ"): bstack1111ll_opy_ (u"ࠪࡪࠬᤁ"),
  bstack1111ll_opy_ (u"ࠫ࡫ࡵࡲࡤࡧࠪᤂ"): bstack1111ll_opy_ (u"ࠬ࡬࡯ࡳࡥࡨࠫᤃ"),
  bstack1111ll_opy_ (u"࠭࡯࡯࡮ࡼࡥࡺࡺ࡯࡮ࡣࡷࡩࠬᤄ"): bstack1111ll_opy_ (u"ࠧࡰࡰ࡯ࡽࡆࡻࡴࡰ࡯ࡤࡸࡪ࠭ᤅ"),
  bstack1111ll_opy_ (u"ࠨࡨࡲࡶࡨ࡫࡬ࡰࡥࡤࡰࠬᤆ"): bstack1111ll_opy_ (u"ࠩࡩࡳࡷࡩࡥ࡭ࡱࡦࡥࡱ࠭ᤇ"),
  bstack1111ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡪࡲࡷࡹ࠭ᤈ"): bstack1111ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࡋࡳࡸࡺࠧᤉ"),
  bstack1111ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡴࡴࡸࡴࠨᤊ"): bstack1111ll_opy_ (u"࠭ࡰࡳࡱࡻࡽࡕࡵࡲࡵࠩᤋ"),
  bstack1111ll_opy_ (u"ࠧࡱࡴࡲࡼࡾࡻࡳࡦࡴࠪᤌ"): bstack1111ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡕࡴࡧࡵࠫᤍ"),
  bstack1111ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡱࡣࡶࡷࠬᤎ"): bstack1111ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡒࡤࡷࡸ࠭ᤏ"),
  bstack1111ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡳࡶࡴࡾࡹࡩࡱࡶࡸࠬᤐ"): bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡔࡷࡵࡸࡺࡊࡲࡷࡹ࠭ᤑ"),
  bstack1111ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡵࡸ࡯ࡹࡻࡳࡳࡷࡺࠧᤒ"): bstack1111ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱࡖࡲࡰࡺࡼࡔࡴࡸࡴࠨᤓ"),
  bstack1111ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡰࡳࡱࡻࡽࡺࡹࡥࡳࠩᤔ"): bstack1111ll_opy_ (u"ࠩ࠰ࡰࡴࡩࡡ࡭ࡒࡵࡳࡽࡿࡕࡴࡧࡵࠫᤕ"),
  bstack1111ll_opy_ (u"ࠪ࠱ࡱࡵࡣࡢ࡮ࡳࡶࡴࡾࡹࡶࡵࡨࡶࠬᤖ"): bstack1111ll_opy_ (u"ࠫ࠲ࡲ࡯ࡤࡣ࡯ࡔࡷࡵࡸࡺࡗࡶࡩࡷ࠭ᤗ"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡴࡷࡵࡸࡺࡲࡤࡷࡸ࠭ᤘ"): bstack1111ll_opy_ (u"࠭࠭࡭ࡱࡦࡥࡱࡖࡲࡰࡺࡼࡔࡦࡹࡳࠨᤙ"),
  bstack1111ll_opy_ (u"ࠧ࠮࡮ࡲࡧࡦࡲࡰࡳࡱࡻࡽࡵࡧࡳࡴࠩᤚ"): bstack1111ll_opy_ (u"ࠨ࠯࡯ࡳࡨࡧ࡬ࡑࡴࡲࡼࡾࡖࡡࡴࡵࠪᤛ"),
  bstack1111ll_opy_ (u"ࠩࡥ࡭ࡳࡧࡲࡺࡲࡤࡸ࡭࠭ᤜ"): bstack1111ll_opy_ (u"ࠪࡦ࡮ࡴࡡࡳࡻࡳࡥࡹ࡮ࠧᤝ"),
  bstack1111ll_opy_ (u"ࠫࡵࡧࡣࡧ࡫࡯ࡩࠬᤞ"): bstack1111ll_opy_ (u"ࠬ࠳ࡰࡢࡥ࠰ࡪ࡮ࡲࡥࠨ᤟"),
  bstack1111ll_opy_ (u"࠭ࡰࡢࡥ࠰ࡪ࡮ࡲࡥࠨᤠ"): bstack1111ll_opy_ (u"ࠧ࠮ࡲࡤࡧ࠲࡬ࡩ࡭ࡧࠪᤡ"),
  bstack1111ll_opy_ (u"ࠨ࠯ࡳࡥࡨ࠳ࡦࡪ࡮ࡨࠫᤢ"): bstack1111ll_opy_ (u"ࠩ࠰ࡴࡦࡩ࠭ࡧ࡫࡯ࡩࠬᤣ"),
  bstack1111ll_opy_ (u"ࠪࡰࡴ࡭ࡦࡪ࡮ࡨࠫᤤ"): bstack1111ll_opy_ (u"ࠫࡱࡵࡧࡧ࡫࡯ࡩࠬᤥ"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯࡭ࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧᤦ"): bstack1111ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨᤧ"),
  bstack1111ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳ࠭ࡳࡧࡳࡩࡦࡺࡥࡳࠩᤨ"): bstack1111ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭ࡓࡧࡳࡩࡦࡺࡥࡳࠩᤩ")
}
bstack11l1ll11lll_opy_ = bstack1111ll_opy_ (u"ࠤ࡫ࡸࡹࡶࡳ࠻࠱࠲࡫࡮ࡺࡨࡶࡤ࠱ࡧࡴࡳ࠯ࡱࡧࡵࡧࡾ࠵ࡣ࡭࡫࠲ࡶࡪࡲࡥࡢࡵࡨࡷ࠴ࡲࡡࡵࡧࡶࡸ࠴ࡪ࡯ࡸࡰ࡯ࡳࡦࡪࠢᤪ")
bstack11l1l1l11l1_opy_ = bstack1111ll_opy_ (u"ࠥ࠳ࡵ࡫ࡲࡤࡻ࠲࡬ࡪࡧ࡬ࡵࡪࡦ࡬ࡪࡩ࡫ࠣᤫ")
bstack11ll1111l_opy_ = bstack1111ll_opy_ (u"ࠦ࡭ࡺࡴࡱࡵ࠽࠳࠴࡫ࡤࡴ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡥࡲࡱ࠴ࡹࡥ࡯ࡦࡢࡷࡩࡱ࡟ࡦࡸࡨࡲࡹࡹࠢ᤬")
bstack1lllll111l_opy_ = bstack1111ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡨࡶࡤ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡷࡥ࠱࡫ࡹࡧ࠭᤭")
bstack11lllll1ll_opy_ = bstack1111ll_opy_ (u"࠭ࡨࡵࡶࡳ࠾࠴࠵ࡨࡶࡤ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲࡀ࠸࠱࠱ࡺࡨ࠴࡮ࡵࡣࠩ᤮")
bstack1ll11l11_opy_ = bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡀ࠯࠰ࡪࡸࡦ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭࠰ࡰࡨࡼࡹࡥࡨࡶࡤࡶࠫ᤯")
bstack1lll1l1111_opy_ = {
  bstack1111ll_opy_ (u"ࠨࡦࡨࡪࡦࡻ࡬ࡵࠩᤰ"): bstack1111ll_opy_ (u"ࠩ࡫ࡹࡧ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩᤱ"),
  bstack1111ll_opy_ (u"ࠪࡹࡸ࠳ࡥࡢࡵࡷࠫᤲ"): bstack1111ll_opy_ (u"ࠫ࡭ࡻࡢ࠮ࡷࡶࡩ࠲ࡵ࡮࡭ࡻ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠭ᤳ"),
  bstack1111ll_opy_ (u"ࠬࡻࡳࠨᤴ"): bstack1111ll_opy_ (u"࠭ࡨࡶࡤ࠰ࡹࡸ࠳࡯࡯࡮ࡼ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳࠧᤵ"),
  bstack1111ll_opy_ (u"ࠧࡦࡷࠪᤶ"): bstack1111ll_opy_ (u"ࠨࡪࡸࡦ࠲࡫ࡵ࠮ࡱࡱࡰࡾ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩᤷ"),
  bstack1111ll_opy_ (u"ࠩ࡬ࡲࠬᤸ"): bstack1111ll_opy_ (u"ࠪ࡬ࡺࡨ࠭ࡢࡲࡶ࠱ࡴࡴ࡬ࡺ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡥࡲࡱ᤹ࠬ"),
  bstack1111ll_opy_ (u"ࠫࡦࡻࠧ᤺"): bstack1111ll_opy_ (u"ࠬ࡮ࡵࡣ࠯ࡤࡴࡸ࡫࠭ࡰࡰ࡯ࡽ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭ࠨ᤻")
}
bstack11l1ll1l1ll_opy_ = {
  bstack1111ll_opy_ (u"࠭ࡣࡳ࡫ࡷ࡭ࡨࡧ࡬ࠨ᤼"): 50,
  bstack1111ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ࠭᤽"): 40,
  bstack1111ll_opy_ (u"ࠨࡹࡤࡶࡳ࡯࡮ࡨࠩ᤾"): 30,
  bstack1111ll_opy_ (u"ࠩ࡬ࡲ࡫ࡵࠧ᤿"): 20,
  bstack1111ll_opy_ (u"ࠪࡨࡪࡨࡵࡨࠩ᥀"): 10
}
bstack11ll1lllll_opy_ = bstack11l1ll1l1ll_opy_[bstack1111ll_opy_ (u"ࠫ࡮ࡴࡦࡰࠩ᥁")]
bstack1ll11ll1l_opy_ = bstack1111ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲ࠲ࡶࡹࡵࡪࡲࡲࡦ࡭ࡥ࡯ࡶ࠲ࠫ᥂")
bstack111l11l11_opy_ = bstack1111ll_opy_ (u"࠭ࡲࡰࡤࡲࡸ࠲ࡶࡹࡵࡪࡲࡲࡦ࡭ࡥ࡯ࡶ࠲ࠫ᥃")
bstack111l11lll_opy_ = bstack1111ll_opy_ (u"ࠧࡣࡧ࡫ࡥࡻ࡫࠭ࡱࡻࡷ࡬ࡴࡴࡡࡨࡧࡱࡸ࠴࠭᥄")
bstack1l1l1ll1l1_opy_ = bstack1111ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴ࠮ࡲࡼࡸ࡭ࡵ࡮ࡢࡩࡨࡲࡹ࠵ࠧ᥅")
bstack1111l11ll_opy_ = bstack1111ll_opy_ (u"ࠩࡓࡰࡪࡧࡳࡦࠢ࡬ࡲࡸࡺࡡ࡭࡮ࠣࡴࡾࡺࡥࡴࡶࠣࡥࡳࡪࠠࡱࡻࡷࡩࡸࡺ࠭ࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࠢࡳࡥࡨࡱࡡࡨࡧࡶ࠲ࠥࡦࡰࡪࡲࠣ࡭ࡳࡹࡴࡢ࡮࡯ࠤࡵࡿࡴࡦࡵࡷࠤࡵࡿࡴࡦࡵࡷ࠱ࡸ࡫࡬ࡦࡰ࡬ࡹࡲࡦࠧ᥆")
bstack11l1l11ll1l_opy_ = [bstack1111ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡘࡗࡊࡘࡎࡂࡏࡈࠫ᥇"), bstack1111ll_opy_ (u"ࠫ࡞ࡕࡕࡓࡡࡘࡗࡊࡘࡎࡂࡏࡈࠫ᥈")]
bstack11l1lll1111_opy_ = [bstack1111ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡆࡉࡃࡆࡕࡖࡣࡐࡋ࡙ࠨ᥉"), bstack1111ll_opy_ (u"࡙࠭ࡐࡗࡕࡣࡆࡉࡃࡆࡕࡖࡣࡐࡋ࡙ࠨ᥊")]
bstack11l111111_opy_ = re.compile(bstack1111ll_opy_ (u"ࠧ࡟࡝࡟ࡠࡼ࠳࡝ࠬ࠼࠱࠮ࠩ࠭᥋"))
bstack111l111l1_opy_ = [
  bstack1111ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡓࡧ࡭ࡦࠩ᥌"),
  bstack1111ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰ࡚ࡪࡸࡳࡪࡱࡱࠫ᥍"),
  bstack1111ll_opy_ (u"ࠪࡨࡪࡼࡩࡤࡧࡑࡥࡲ࡫ࠧ᥎"),
  bstack1111ll_opy_ (u"ࠫࡳ࡫ࡷࡄࡱࡰࡱࡦࡴࡤࡕ࡫ࡰࡩࡴࡻࡴࠨ᥏"),
  bstack1111ll_opy_ (u"ࠬࡧࡰࡱࠩᥐ"),
  bstack1111ll_opy_ (u"࠭ࡵࡥ࡫ࡧࠫᥑ"),
  bstack1111ll_opy_ (u"ࠧ࡭ࡣࡱ࡫ࡺࡧࡧࡦࠩᥒ"),
  bstack1111ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡥࠨᥓ"),
  bstack1111ll_opy_ (u"ࠩࡲࡶ࡮࡫࡮ࡵࡣࡷ࡭ࡴࡴࠧᥔ"),
  bstack1111ll_opy_ (u"ࠪࡥࡺࡺ࡯ࡘࡧࡥࡺ࡮࡫ࡷࠨᥕ"),
  bstack1111ll_opy_ (u"ࠫࡳࡵࡒࡦࡵࡨࡸࠬᥖ"), bstack1111ll_opy_ (u"ࠬ࡬ࡵ࡭࡮ࡕࡩࡸ࡫ࡴࠨᥗ"),
  bstack1111ll_opy_ (u"࠭ࡣ࡭ࡧࡤࡶࡘࡿࡳࡵࡧࡰࡊ࡮ࡲࡥࡴࠩᥘ"),
  bstack1111ll_opy_ (u"ࠧࡦࡸࡨࡲࡹ࡚ࡩ࡮࡫ࡱ࡫ࡸ࠭ᥙ"),
  bstack1111ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡑࡧࡵࡪࡴࡸ࡭ࡢࡰࡦࡩࡑࡵࡧࡨ࡫ࡱ࡫ࠬᥚ"),
  bstack1111ll_opy_ (u"ࠩࡲࡸ࡭࡫ࡲࡂࡲࡳࡷࠬᥛ"),
  bstack1111ll_opy_ (u"ࠪࡴࡷ࡯࡮ࡵࡒࡤ࡫ࡪ࡙࡯ࡶࡴࡦࡩࡔࡴࡆࡪࡰࡧࡊࡦ࡯࡬ࡶࡴࡨࠫᥜ"),
  bstack1111ll_opy_ (u"ࠫࡦࡶࡰࡂࡥࡷ࡭ࡻ࡯ࡴࡺࠩᥝ"), bstack1111ll_opy_ (u"ࠬࡧࡰࡱࡒࡤࡧࡰࡧࡧࡦࠩᥞ"), bstack1111ll_opy_ (u"࠭ࡡࡱࡲ࡚ࡥ࡮ࡺࡁࡤࡶ࡬ࡺ࡮ࡺࡹࠨᥟ"), bstack1111ll_opy_ (u"ࠧࡢࡲࡳ࡛ࡦ࡯ࡴࡑࡣࡦ࡯ࡦ࡭ࡥࠨᥠ"), bstack1111ll_opy_ (u"ࠨࡣࡳࡴ࡜ࡧࡩࡵࡆࡸࡶࡦࡺࡩࡰࡰࠪᥡ"),
  bstack1111ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࡔࡨࡥࡩࡿࡔࡪ࡯ࡨࡳࡺࡺࠧᥢ"),
  bstack1111ll_opy_ (u"ࠪࡥࡱࡲ࡯ࡸࡖࡨࡷࡹࡖࡡࡤ࡭ࡤ࡫ࡪࡹࠧᥣ"),
  bstack1111ll_opy_ (u"ࠫࡦࡴࡤࡳࡱ࡬ࡨࡈࡵࡶࡦࡴࡤ࡫ࡪ࠭ᥤ"), bstack1111ll_opy_ (u"ࠬࡧ࡮ࡥࡴࡲ࡭ࡩࡉ࡯ࡷࡧࡵࡥ࡬࡫ࡅ࡯ࡦࡌࡲࡹ࡫࡮ࡵࠩᥥ"),
  bstack1111ll_opy_ (u"࠭ࡡ࡯ࡦࡵࡳ࡮ࡪࡄࡦࡸ࡬ࡧࡪࡘࡥࡢࡦࡼࡘ࡮ࡳࡥࡰࡷࡷࠫᥦ"),
  bstack1111ll_opy_ (u"ࠧࡢࡦࡥࡔࡴࡸࡴࠨᥧ"),
  bstack1111ll_opy_ (u"ࠨࡣࡱࡨࡷࡵࡩࡥࡆࡨࡺ࡮ࡩࡥࡔࡱࡦ࡯ࡪࡺࠧᥨ"),
  bstack1111ll_opy_ (u"ࠩࡤࡲࡩࡸ࡯ࡪࡦࡌࡲࡸࡺࡡ࡭࡮ࡗ࡭ࡲ࡫࡯ࡶࡶࠪᥩ"),
  bstack1111ll_opy_ (u"ࠪࡥࡳࡪࡲࡰ࡫ࡧࡍࡳࡹࡴࡢ࡮࡯ࡔࡦࡺࡨࠨᥪ"),
  bstack1111ll_opy_ (u"ࠫࡦࡼࡤࠨᥫ"), bstack1111ll_opy_ (u"ࠬࡧࡶࡥࡎࡤࡹࡳࡩࡨࡕ࡫ࡰࡩࡴࡻࡴࠨᥬ"), bstack1111ll_opy_ (u"࠭ࡡࡷࡦࡕࡩࡦࡪࡹࡕ࡫ࡰࡩࡴࡻࡴࠨᥭ"), bstack1111ll_opy_ (u"ࠧࡢࡸࡧࡅࡷ࡭ࡳࠨ᥮"),
  bstack1111ll_opy_ (u"ࠨࡷࡶࡩࡐ࡫ࡹࡴࡶࡲࡶࡪ࠭᥯"), bstack1111ll_opy_ (u"ࠩ࡮ࡩࡾࡹࡴࡰࡴࡨࡔࡦࡺࡨࠨᥰ"), bstack1111ll_opy_ (u"ࠪ࡯ࡪࡿࡳࡵࡱࡵࡩࡕࡧࡳࡴࡹࡲࡶࡩ࠭ᥱ"),
  bstack1111ll_opy_ (u"ࠫࡰ࡫ࡹࡂ࡮࡬ࡥࡸ࠭ᥲ"), bstack1111ll_opy_ (u"ࠬࡱࡥࡺࡒࡤࡷࡸࡽ࡯ࡳࡦࠪᥳ"),
  bstack1111ll_opy_ (u"࠭ࡣࡩࡴࡲࡱࡪࡪࡲࡪࡸࡨࡶࡊࡾࡥࡤࡷࡷࡥࡧࡲࡥࠨᥴ"), bstack1111ll_opy_ (u"ࠧࡤࡪࡵࡳࡲ࡫ࡤࡳ࡫ࡹࡩࡷࡇࡲࡨࡵࠪ᥵"), bstack1111ll_opy_ (u"ࠨࡥ࡫ࡶࡴࡳࡥࡥࡴ࡬ࡺࡪࡸࡅࡹࡧࡦࡹࡹࡧࡢ࡭ࡧࡇ࡭ࡷ࠭᥶"), bstack1111ll_opy_ (u"ࠩࡦ࡬ࡷࡵ࡭ࡦࡦࡵ࡭ࡻ࡫ࡲࡄࡪࡵࡳࡲ࡫ࡍࡢࡲࡳ࡭ࡳ࡭ࡆࡪ࡮ࡨࠫ᥷"), bstack1111ll_opy_ (u"ࠪࡧ࡭ࡸ࡯࡮ࡧࡧࡶ࡮ࡼࡥࡳࡗࡶࡩࡘࡿࡳࡵࡧࡰࡉࡽ࡫ࡣࡶࡶࡤࡦࡱ࡫ࠧ᥸"),
  bstack1111ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࡨࡷ࡯ࡶࡦࡴࡓࡳࡷࡺࠧ᥹"), bstack1111ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࡩࡸࡩࡷࡧࡵࡔࡴࡸࡴࡴࠩ᥺"),
  bstack1111ll_opy_ (u"࠭ࡣࡩࡴࡲࡱࡪࡪࡲࡪࡸࡨࡶࡉ࡯ࡳࡢࡤ࡯ࡩࡇࡻࡩ࡭ࡦࡆ࡬ࡪࡩ࡫ࠨ᥻"),
  bstack1111ll_opy_ (u"ࠧࡢࡷࡷࡳ࡜࡫ࡢࡷ࡫ࡨࡻ࡙࡯࡭ࡦࡱࡸࡸࠬ᥼"),
  bstack1111ll_opy_ (u"ࠨ࡫ࡱࡸࡪࡴࡴࡂࡥࡷ࡭ࡴࡴࠧ᥽"), bstack1111ll_opy_ (u"ࠩ࡬ࡲࡹ࡫࡮ࡵࡅࡤࡸࡪ࡭࡯ࡳࡻࠪ᥾"), bstack1111ll_opy_ (u"ࠪ࡭ࡳࡺࡥ࡯ࡶࡉࡰࡦ࡭ࡳࠨ᥿"), bstack1111ll_opy_ (u"ࠫࡴࡶࡴࡪࡱࡱࡥࡱࡏ࡮ࡵࡧࡱࡸࡆࡸࡧࡶ࡯ࡨࡲࡹࡹࠧᦀ"),
  bstack1111ll_opy_ (u"ࠬࡪ࡯࡯ࡶࡖࡸࡴࡶࡁࡱࡲࡒࡲࡗ࡫ࡳࡦࡶࠪᦁ"),
  bstack1111ll_opy_ (u"࠭ࡵ࡯࡫ࡦࡳࡩ࡫ࡋࡦࡻࡥࡳࡦࡸࡤࠨᦂ"), bstack1111ll_opy_ (u"ࠧࡳࡧࡶࡩࡹࡑࡥࡺࡤࡲࡥࡷࡪࠧᦃ"),
  bstack1111ll_opy_ (u"ࠨࡰࡲࡗ࡮࡭࡮ࠨᦄ"),
  bstack1111ll_opy_ (u"ࠩ࡬࡫ࡳࡵࡲࡦࡗࡱ࡭ࡲࡶ࡯ࡳࡶࡤࡲࡹ࡜ࡩࡦࡹࡶࠫᦅ"),
  bstack1111ll_opy_ (u"ࠪࡨ࡮ࡹࡡࡣ࡮ࡨࡅࡳࡪࡲࡰ࡫ࡧ࡛ࡦࡺࡣࡩࡧࡵࡷࠬᦆ"),
  bstack1111ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠫᦇ"),
  bstack1111ll_opy_ (u"ࠬࡸࡥࡤࡴࡨࡥࡹ࡫ࡃࡩࡴࡲࡱࡪࡊࡲࡪࡸࡨࡶࡘ࡫ࡳࡴ࡫ࡲࡲࡸ࠭ᦈ"),
  bstack1111ll_opy_ (u"࠭࡮ࡢࡶ࡬ࡺࡪ࡝ࡥࡣࡕࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࠬᦉ"),
  bstack1111ll_opy_ (u"ࠧࡢࡰࡧࡶࡴ࡯ࡤࡔࡥࡵࡩࡪࡴࡳࡩࡱࡷࡔࡦࡺࡨࠨᦊ"),
  bstack1111ll_opy_ (u"ࠨࡰࡨࡸࡼࡵࡲ࡬ࡕࡳࡩࡪࡪࠧᦋ"),
  bstack1111ll_opy_ (u"ࠩࡪࡴࡸࡋ࡮ࡢࡤ࡯ࡩࡩ࠭ᦌ"),
  bstack1111ll_opy_ (u"ࠪ࡭ࡸࡎࡥࡢࡦ࡯ࡩࡸࡹࠧᦍ"),
  bstack1111ll_opy_ (u"ࠫࡦࡪࡢࡆࡺࡨࡧ࡙࡯࡭ࡦࡱࡸࡸࠬᦎ"),
  bstack1111ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡩࡘࡩࡲࡪࡲࡷࠫᦏ"),
  bstack1111ll_opy_ (u"࠭ࡳ࡬࡫ࡳࡈࡪࡼࡩࡤࡧࡌࡲ࡮ࡺࡩࡢ࡮࡬ࡾࡦࡺࡩࡰࡰࠪᦐ"),
  bstack1111ll_opy_ (u"ࠧࡢࡷࡷࡳࡌࡸࡡ࡯ࡶࡓࡩࡷࡳࡩࡴࡵ࡬ࡳࡳࡹࠧᦑ"),
  bstack1111ll_opy_ (u"ࠨࡣࡱࡨࡷࡵࡩࡥࡐࡤࡸࡺࡸࡡ࡭ࡑࡵ࡭ࡪࡴࡴࡢࡶ࡬ࡳࡳ࠭ᦒ"),
  bstack1111ll_opy_ (u"ࠩࡶࡽࡸࡺࡥ࡮ࡒࡲࡶࡹ࠭ᦓ"),
  bstack1111ll_opy_ (u"ࠪࡶࡪࡳ࡯ࡵࡧࡄࡨࡧࡎ࡯ࡴࡶࠪᦔ"),
  bstack1111ll_opy_ (u"ࠫࡸࡱࡩࡱࡗࡱࡰࡴࡩ࡫ࠨᦕ"), bstack1111ll_opy_ (u"ࠬࡻ࡮࡭ࡱࡦ࡯࡙ࡿࡰࡦࠩᦖ"), bstack1111ll_opy_ (u"࠭ࡵ࡯࡮ࡲࡧࡰࡑࡥࡺࠩᦗ"),
  bstack1111ll_opy_ (u"ࠧࡢࡷࡷࡳࡑࡧࡵ࡯ࡥ࡫ࠫᦘ"),
  bstack1111ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡒ࡯ࡨࡥࡤࡸࡈࡧࡰࡵࡷࡵࡩࠬᦙ"),
  bstack1111ll_opy_ (u"ࠩࡸࡲ࡮ࡴࡳࡵࡣ࡯ࡰࡔࡺࡨࡦࡴࡓࡥࡨࡱࡡࡨࡧࡶࠫᦚ"),
  bstack1111ll_opy_ (u"ࠪࡨ࡮ࡹࡡࡣ࡮ࡨ࡛࡮ࡴࡤࡰࡹࡄࡲ࡮ࡳࡡࡵ࡫ࡲࡲࠬᦛ"),
  bstack1111ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡗࡳࡴࡲࡳࡗࡧࡵࡷ࡮ࡵ࡮ࠨᦜ"),
  bstack1111ll_opy_ (u"ࠬ࡫࡮ࡧࡱࡵࡧࡪࡇࡰࡱࡋࡱࡷࡹࡧ࡬࡭ࠩᦝ"),
  bstack1111ll_opy_ (u"࠭ࡥ࡯ࡵࡸࡶࡪ࡝ࡥࡣࡸ࡬ࡩࡼࡹࡈࡢࡸࡨࡔࡦ࡭ࡥࡴࠩᦞ"), bstack1111ll_opy_ (u"ࠧࡸࡧࡥࡺ࡮࡫ࡷࡅࡧࡹࡸࡴࡵ࡬ࡴࡒࡲࡶࡹ࠭ᦟ"), bstack1111ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡘࡧࡥࡺ࡮࡫ࡷࡅࡧࡷࡥ࡮ࡲࡳࡄࡱ࡯ࡰࡪࡩࡴࡪࡱࡱࠫᦠ"),
  bstack1111ll_opy_ (u"ࠩࡵࡩࡲࡵࡴࡦࡃࡳࡴࡸࡉࡡࡤࡪࡨࡐ࡮ࡳࡩࡵࠩᦡ"),
  bstack1111ll_opy_ (u"ࠪࡧࡦࡲࡥ࡯ࡦࡤࡶࡋࡵࡲ࡮ࡣࡷࠫᦢ"),
  bstack1111ll_opy_ (u"ࠫࡧࡻ࡮ࡥ࡮ࡨࡍࡩ࠭ᦣ"),
  bstack1111ll_opy_ (u"ࠬࡲࡡࡶࡰࡦ࡬࡙࡯࡭ࡦࡱࡸࡸࠬᦤ"),
  bstack1111ll_opy_ (u"࠭࡬ࡰࡥࡤࡸ࡮ࡵ࡮ࡔࡧࡵࡺ࡮ࡩࡥࡴࡇࡱࡥࡧࡲࡥࡥࠩᦥ"), bstack1111ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡹ࡯࡯࡯ࡕࡨࡶࡻ࡯ࡣࡦࡵࡄࡹࡹ࡮࡯ࡳ࡫ࡽࡩࡩ࠭ᦦ"),
  bstack1111ll_opy_ (u"ࠨࡣࡸࡸࡴࡇࡣࡤࡧࡳࡸࡆࡲࡥࡳࡶࡶࠫᦧ"), bstack1111ll_opy_ (u"ࠩࡤࡹࡹࡵࡄࡪࡵࡰ࡭ࡸࡹࡁ࡭ࡧࡵࡸࡸ࠭ᦨ"),
  bstack1111ll_opy_ (u"ࠪࡲࡦࡺࡩࡷࡧࡌࡲࡸࡺࡲࡶ࡯ࡨࡲࡹࡹࡌࡪࡤࠪᦩ"),
  bstack1111ll_opy_ (u"ࠫࡳࡧࡴࡪࡸࡨ࡛ࡪࡨࡔࡢࡲࠪᦪ"),
  bstack1111ll_opy_ (u"ࠬࡹࡡࡧࡣࡵ࡭ࡎࡴࡩࡵ࡫ࡤࡰ࡚ࡸ࡬ࠨᦫ"), bstack1111ll_opy_ (u"࠭ࡳࡢࡨࡤࡶ࡮ࡇ࡬࡭ࡱࡺࡔࡴࡶࡵࡱࡵࠪ᦬"), bstack1111ll_opy_ (u"ࠧࡴࡣࡩࡥࡷ࡯ࡉࡨࡰࡲࡶࡪࡌࡲࡢࡷࡧ࡛ࡦࡸ࡮ࡪࡰࡪࠫ᦭"), bstack1111ll_opy_ (u"ࠨࡵࡤࡪࡦࡸࡩࡐࡲࡨࡲࡑ࡯࡮࡬ࡵࡌࡲࡇࡧࡣ࡬ࡩࡵࡳࡺࡴࡤࠨ᦮"),
  bstack1111ll_opy_ (u"ࠩ࡮ࡩࡪࡶࡋࡦࡻࡆ࡬ࡦ࡯࡮ࡴࠩ᦯"),
  bstack1111ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭࡫ࡽࡥࡧࡲࡥࡔࡶࡵ࡭ࡳ࡭ࡳࡅ࡫ࡵࠫᦰ"),
  bstack1111ll_opy_ (u"ࠫࡵࡸ࡯ࡤࡧࡶࡷࡆࡸࡧࡶ࡯ࡨࡲࡹࡹࠧᦱ"),
  bstack1111ll_opy_ (u"ࠬ࡯࡮ࡵࡧࡵࡏࡪࡿࡄࡦ࡮ࡤࡽࠬᦲ"),
  bstack1111ll_opy_ (u"࠭ࡳࡩࡱࡺࡍࡔ࡙ࡌࡰࡩࠪᦳ"),
  bstack1111ll_opy_ (u"ࠧࡴࡧࡱࡨࡐ࡫ࡹࡔࡶࡵࡥࡹ࡫ࡧࡺࠩᦴ"),
  bstack1111ll_opy_ (u"ࠨࡹࡨࡦࡰ࡯ࡴࡓࡧࡶࡴࡴࡴࡳࡦࡖ࡬ࡱࡪࡵࡵࡵࠩᦵ"), bstack1111ll_opy_ (u"ࠩࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹ࡝ࡡࡪࡶࡗ࡭ࡲ࡫࡯ࡶࡶࠪᦶ"),
  bstack1111ll_opy_ (u"ࠪࡶࡪࡳ࡯ࡵࡧࡇࡩࡧࡻࡧࡑࡴࡲࡼࡾ࠭ᦷ"),
  bstack1111ll_opy_ (u"ࠫࡪࡴࡡࡣ࡮ࡨࡅࡸࡿ࡮ࡤࡇࡻࡩࡨࡻࡴࡦࡈࡵࡳࡲࡎࡴࡵࡲࡶࠫᦸ"),
  bstack1111ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡏࡳ࡬ࡉࡡࡱࡶࡸࡶࡪ࠭ᦹ"),
  bstack1111ll_opy_ (u"࠭ࡷࡦࡤ࡮࡭ࡹࡊࡥࡣࡷࡪࡔࡷࡵࡸࡺࡒࡲࡶࡹ࠭ᦺ"),
  bstack1111ll_opy_ (u"ࠧࡧࡷ࡯ࡰࡈࡵ࡮ࡵࡧࡻࡸࡑ࡯ࡳࡵࠩᦻ"),
  bstack1111ll_opy_ (u"ࠨࡹࡤ࡭ࡹࡌ࡯ࡳࡃࡳࡴࡘࡩࡲࡪࡲࡷࠫᦼ"),
  bstack1111ll_opy_ (u"ࠩࡺࡩࡧࡼࡩࡦࡹࡆࡳࡳࡴࡥࡤࡶࡕࡩࡹࡸࡩࡦࡵࠪᦽ"),
  bstack1111ll_opy_ (u"ࠪࡥࡵࡶࡎࡢ࡯ࡨࠫᦾ"),
  bstack1111ll_opy_ (u"ࠫࡨࡻࡳࡵࡱࡰࡗࡘࡒࡃࡦࡴࡷࠫᦿ"),
  bstack1111ll_opy_ (u"ࠬࡺࡡࡱ࡙࡬ࡸ࡭࡙ࡨࡰࡴࡷࡔࡷ࡫ࡳࡴࡆࡸࡶࡦࡺࡩࡰࡰࠪᧀ"),
  bstack1111ll_opy_ (u"࠭ࡳࡤࡣ࡯ࡩࡋࡧࡣࡵࡱࡵࠫᧁ"),
  bstack1111ll_opy_ (u"ࠧࡸࡦࡤࡐࡴࡩࡡ࡭ࡒࡲࡶࡹ࠭ᧂ"),
  bstack1111ll_opy_ (u"ࠨࡵ࡫ࡳࡼ࡞ࡣࡰࡦࡨࡐࡴ࡭ࠧᧃ"),
  bstack1111ll_opy_ (u"ࠩ࡬ࡳࡸࡏ࡮ࡴࡶࡤࡰࡱࡖࡡࡶࡵࡨࠫᧄ"),
  bstack1111ll_opy_ (u"ࠪࡼࡨࡵࡤࡦࡅࡲࡲ࡫࡯ࡧࡇ࡫࡯ࡩࠬᧅ"),
  bstack1111ll_opy_ (u"ࠫࡰ࡫ࡹࡤࡪࡤ࡭ࡳࡖࡡࡴࡵࡺࡳࡷࡪࠧᧆ"),
  bstack1111ll_opy_ (u"ࠬࡻࡳࡦࡒࡵࡩࡧࡻࡩ࡭ࡶ࡚ࡈࡆ࠭ᧇ"),
  bstack1111ll_opy_ (u"࠭ࡰࡳࡧࡹࡩࡳࡺࡗࡅࡃࡄࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࡹࠧᧈ"),
  bstack1111ll_opy_ (u"ࠧࡸࡧࡥࡈࡷ࡯ࡶࡦࡴࡄ࡫ࡪࡴࡴࡖࡴ࡯ࠫᧉ"),
  bstack1111ll_opy_ (u"ࠨ࡭ࡨࡽࡨ࡮ࡡࡪࡰࡓࡥࡹ࡮ࠧ᧊"),
  bstack1111ll_opy_ (u"ࠩࡸࡷࡪࡔࡥࡸ࡙ࡇࡅࠬ᧋"),
  bstack1111ll_opy_ (u"ࠪࡻࡩࡧࡌࡢࡷࡱࡧ࡭࡚ࡩ࡮ࡧࡲࡹࡹ࠭᧌"), bstack1111ll_opy_ (u"ࠫࡼࡪࡡࡄࡱࡱࡲࡪࡩࡴࡪࡱࡱࡘ࡮ࡳࡥࡰࡷࡷࠫ᧍"),
  bstack1111ll_opy_ (u"ࠬࡾࡣࡰࡦࡨࡓࡷ࡭ࡉࡥࠩ᧎"), bstack1111ll_opy_ (u"࠭ࡸࡤࡱࡧࡩࡘ࡯ࡧ࡯࡫ࡱ࡫ࡎࡪࠧ᧏"),
  bstack1111ll_opy_ (u"ࠧࡶࡲࡧࡥࡹ࡫ࡤࡘࡆࡄࡆࡺࡴࡤ࡭ࡧࡌࡨࠬ᧐"),
  bstack1111ll_opy_ (u"ࠨࡴࡨࡷࡪࡺࡏ࡯ࡕࡨࡷࡸ࡯࡯࡯ࡕࡷࡥࡷࡺࡏ࡯࡮ࡼࠫ᧑"),
  bstack1111ll_opy_ (u"ࠩࡦࡳࡲࡳࡡ࡯ࡦࡗ࡭ࡲ࡫࡯ࡶࡶࡶࠫ᧒"),
  bstack1111ll_opy_ (u"ࠪࡻࡩࡧࡓࡵࡣࡵࡸࡺࡶࡒࡦࡶࡵ࡭ࡪࡹࠧ᧓"), bstack1111ll_opy_ (u"ࠫࡼࡪࡡࡔࡶࡤࡶࡹࡻࡰࡓࡧࡷࡶࡾࡏ࡮ࡵࡧࡵࡺࡦࡲࠧ᧔"),
  bstack1111ll_opy_ (u"ࠬࡩ࡯࡯ࡰࡨࡧࡹࡎࡡࡳࡦࡺࡥࡷ࡫ࡋࡦࡻࡥࡳࡦࡸࡤࠨ᧕"),
  bstack1111ll_opy_ (u"࠭࡭ࡢࡺࡗࡽࡵ࡯࡮ࡨࡈࡵࡩࡶࡻࡥ࡯ࡥࡼࠫ᧖"),
  bstack1111ll_opy_ (u"ࠧࡴ࡫ࡰࡴࡱ࡫ࡉࡴࡘ࡬ࡷ࡮ࡨ࡬ࡦࡅ࡫ࡩࡨࡱࠧ᧗"),
  bstack1111ll_opy_ (u"ࠨࡷࡶࡩࡈࡧࡲࡵࡪࡤ࡫ࡪ࡙ࡳ࡭ࠩ᧘"),
  bstack1111ll_opy_ (u"ࠩࡶ࡬ࡴࡻ࡬ࡥࡗࡶࡩࡘ࡯࡮ࡨ࡮ࡨࡸࡴࡴࡔࡦࡵࡷࡑࡦࡴࡡࡨࡧࡵࠫ᧙"),
  bstack1111ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࡋ࡚ࡈࡕ࠭᧚"),
  bstack1111ll_opy_ (u"ࠫࡦࡲ࡬ࡰࡹࡗࡳࡺࡩࡨࡊࡦࡈࡲࡷࡵ࡬࡭ࠩ᧛"),
  bstack1111ll_opy_ (u"ࠬ࡯ࡧ࡯ࡱࡵࡩࡍ࡯ࡤࡥࡧࡱࡅࡵ࡯ࡐࡰ࡮࡬ࡧࡾࡋࡲࡳࡱࡵࠫ᧜"),
  bstack1111ll_opy_ (u"࠭࡭ࡰࡥ࡮ࡐࡴࡩࡡࡵ࡫ࡲࡲࡆࡶࡰࠨ᧝"),
  bstack1111ll_opy_ (u"ࠧ࡭ࡱࡪࡧࡦࡺࡆࡰࡴࡰࡥࡹ࠭᧞"), bstack1111ll_opy_ (u"ࠨ࡮ࡲ࡫ࡨࡧࡴࡇ࡫࡯ࡸࡪࡸࡓࡱࡧࡦࡷࠬ᧟"),
  bstack1111ll_opy_ (u"ࠩࡤࡰࡱࡵࡷࡅࡧ࡯ࡥࡾࡇࡤࡣࠩ᧠"),
  bstack1111ll_opy_ (u"ࠪࡨ࡮ࡹࡡࡣ࡮ࡨࡍࡩࡒ࡯ࡤࡣࡷࡳࡷࡇࡵࡵࡱࡦࡳࡲࡶ࡬ࡦࡶ࡬ࡳࡳ࠭᧡")
]
bstack11111l11_opy_ = bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵ࠽࠳࠴ࡧࡰࡪ࠯ࡦࡰࡴࡻࡤ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰ࠳ࡦࡶࡰ࠮ࡣࡸࡸࡴࡳࡡࡵࡧ࠲ࡹࡵࡲ࡯ࡢࡦࠪ᧢")
bstack11l11l11ll_opy_ = [bstack1111ll_opy_ (u"ࠬ࠴ࡡࡱ࡭ࠪ᧣"), bstack1111ll_opy_ (u"࠭࠮ࡢࡣࡥࠫ᧤"), bstack1111ll_opy_ (u"ࠧ࠯࡫ࡳࡥࠬ᧥")]
bstack111lll111_opy_ = [bstack1111ll_opy_ (u"ࠨ࡫ࡧࠫ᧦"), bstack1111ll_opy_ (u"ࠩࡳࡥࡹ࡮ࠧ᧧"), bstack1111ll_opy_ (u"ࠪࡧࡺࡹࡴࡰ࡯ࡢ࡭ࡩ࠭᧨"), bstack1111ll_opy_ (u"ࠫࡸ࡮ࡡࡳࡧࡤࡦࡱ࡫࡟ࡪࡦࠪ᧩")]
bstack1ll1ll111l_opy_ = {
  bstack1111ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬ᧪"): bstack1111ll_opy_ (u"࠭ࡧࡰࡱࡪ࠾ࡨ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠫ᧫"),
  bstack1111ll_opy_ (u"ࠧࡧ࡫ࡵࡩ࡫ࡵࡸࡐࡲࡷ࡭ࡴࡴࡳࠨ᧬"): bstack1111ll_opy_ (u"ࠨ࡯ࡲࡾ࠿࡬ࡩࡳࡧࡩࡳࡽࡕࡰࡵ࡫ࡲࡲࡸ࠭᧭"),
  bstack1111ll_opy_ (u"ࠩࡨࡨ࡬࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧ᧮"): bstack1111ll_opy_ (u"ࠪࡱࡸࡀࡥࡥࡩࡨࡓࡵࡺࡩࡰࡰࡶࠫ᧯"),
  bstack1111ll_opy_ (u"ࠫ࡮࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧ᧰"): bstack1111ll_opy_ (u"ࠬࡹࡥ࠻࡫ࡨࡓࡵࡺࡩࡰࡰࡶࠫ᧱"),
  bstack1111ll_opy_ (u"࠭ࡳࡢࡨࡤࡶ࡮ࡕࡰࡵ࡫ࡲࡲࡸ࠭᧲"): bstack1111ll_opy_ (u"ࠧࡴࡣࡩࡥࡷ࡯࠮ࡰࡲࡷ࡭ࡴࡴࡳࠨ᧳")
}
bstack1l1l1l1lll_opy_ = [
  bstack1111ll_opy_ (u"ࠨࡩࡲࡳ࡬ࡀࡣࡩࡴࡲࡱࡪࡕࡰࡵ࡫ࡲࡲࡸ࠭᧴"),
  bstack1111ll_opy_ (u"ࠩࡰࡳࡿࡀࡦࡪࡴࡨࡪࡴࡾࡏࡱࡶ࡬ࡳࡳࡹࠧ᧵"),
  bstack1111ll_opy_ (u"ࠪࡱࡸࡀࡥࡥࡩࡨࡓࡵࡺࡩࡰࡰࡶࠫ᧶"),
  bstack1111ll_opy_ (u"ࠫࡸ࡫࠺ࡪࡧࡒࡴࡹ࡯࡯࡯ࡵࠪ᧷"),
  bstack1111ll_opy_ (u"ࠬࡹࡡࡧࡣࡵ࡭࠳ࡵࡰࡵ࡫ࡲࡲࡸ࠭᧸"),
]
bstack1l111l1l_opy_ = bstack11lllll1l_opy_ + bstack11l1ll11l1l_opy_ + bstack111l111l1_opy_
bstack1l1l1ll1_opy_ = [
  bstack1111ll_opy_ (u"࠭࡞࡭ࡱࡦࡥࡱ࡮࡯ࡴࡶࠧࠫ᧹"),
  bstack1111ll_opy_ (u"ࠧ࡟ࡤࡶ࠱ࡱࡵࡣࡢ࡮࠱ࡧࡴࡳࠤࠨ᧺"),
  bstack1111ll_opy_ (u"ࠨࡠ࠴࠶࠼࠴ࠧ᧻"),
  bstack1111ll_opy_ (u"ࠩࡡ࠵࠵࠴ࠧ᧼"),
  bstack1111ll_opy_ (u"ࠪࡢ࠶࠽࠲࠯࠳࡞࠺࠲࠿࡝࠯ࠩ᧽"),
  bstack1111ll_opy_ (u"ࠫࡣ࠷࠷࠳࠰࠵࡟࠵࠳࠹࡞࠰ࠪ᧾"),
  bstack1111ll_opy_ (u"ࠬࡤ࠱࠸࠴࠱࠷ࡠ࠶࠭࠲࡟࠱ࠫ᧿"),
  bstack1111ll_opy_ (u"࠭࡞࠲࠻࠵࠲࠶࠼࠸࠯ࠩᨀ")
]
bstack11ll1111lll_opy_ = bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡀ࠯࠰ࡣࡳ࡭࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭ࠨᨁ")
bstack1ll1lll11_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠴ࡼ࠱࠰ࡧࡹࡩࡳࡺࠧᨂ")
bstack1111l1ll1_opy_ = [ bstack1111ll_opy_ (u"ࠩࡤࡹࡹࡵ࡭ࡢࡶࡨࠫᨃ") ]
bstack1ll1ll1l1_opy_ = [ bstack1111ll_opy_ (u"ࠪࡥࡵࡶ࠭ࡢࡷࡷࡳࡲࡧࡴࡦࠩᨄ") ]
bstack1111l11l_opy_ = [bstack1111ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࠨᨅ")]
bstack1l11l11l1_opy_ = [ bstack1111ll_opy_ (u"ࠬࡵࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠬᨆ") ]
bstack111ll1l1l_opy_ = bstack1111ll_opy_ (u"࠭ࡓࡅࡍࡖࡩࡹࡻࡰࠨᨇ")
bstack1ll11l111_opy_ = bstack1111ll_opy_ (u"ࠧࡔࡆࡎࡘࡪࡹࡴࡂࡶࡷࡩࡲࡶࡴࡦࡦࠪᨈ")
bstack1l1l1l1ll_opy_ = bstack1111ll_opy_ (u"ࠨࡕࡇࡏ࡙࡫ࡳࡵࡕࡸࡧࡨ࡫ࡳࡴࡨࡸࡰࠬᨉ")
bstack11llllll_opy_ = bstack1111ll_opy_ (u"ࠩ࠷࠲࠵࠴࠰ࠨᨊ")
bstack1lll1llll_opy_ = [
  bstack1111ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡇࡃࡌࡐࡊࡊࠧᨋ"),
  bstack1111ll_opy_ (u"ࠫࡊࡘࡒࡠࡖࡌࡑࡊࡊ࡟ࡐࡗࡗࠫᨌ"),
  bstack1111ll_opy_ (u"ࠬࡋࡒࡓࡡࡅࡐࡔࡉࡋࡆࡆࡢࡆ࡞ࡥࡃࡍࡋࡈࡒ࡙࠭ᨍ"),
  bstack1111ll_opy_ (u"࠭ࡅࡓࡔࡢࡒࡊ࡚ࡗࡐࡔࡎࡣࡈࡎࡁࡏࡉࡈࡈࠬᨎ"),
  bstack1111ll_opy_ (u"ࠧࡆࡔࡕࡣࡘࡕࡃࡌࡇࡗࡣࡓࡕࡔࡠࡅࡒࡒࡓࡋࡃࡕࡇࡇࠫᨏ"),
  bstack1111ll_opy_ (u"ࠨࡇࡕࡖࡤࡉࡏࡏࡐࡈࡇ࡙ࡏࡏࡏࡡࡆࡐࡔ࡙ࡅࡅࠩᨐ"),
  bstack1111ll_opy_ (u"ࠩࡈࡖࡗࡥࡃࡐࡐࡑࡉࡈ࡚ࡉࡐࡐࡢࡖࡊ࡙ࡅࡕࠩᨑ"),
  bstack1111ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡄࡑࡑࡒࡊࡉࡔࡊࡑࡑࡣࡗࡋࡆࡖࡕࡈࡈࠬᨒ"),
  bstack1111ll_opy_ (u"ࠫࡊࡘࡒࡠࡅࡒࡒࡓࡋࡃࡕࡋࡒࡒࡤࡇࡂࡐࡔࡗࡉࡉ࠭ᨓ"),
  bstack1111ll_opy_ (u"ࠬࡋࡒࡓࡡࡆࡓࡓࡔࡅࡄࡖࡌࡓࡓࡥࡆࡂࡋࡏࡉࡉ࠭ᨔ"),
  bstack1111ll_opy_ (u"࠭ࡅࡓࡔࡢࡒࡆࡓࡅࡠࡐࡒࡘࡤࡘࡅࡔࡑࡏ࡚ࡊࡊࠧᨕ"),
  bstack1111ll_opy_ (u"ࠧࡆࡔࡕࡣࡆࡊࡄࡓࡇࡖࡗࡤࡏࡎࡗࡃࡏࡍࡉ࠭ᨖ"),
  bstack1111ll_opy_ (u"ࠨࡇࡕࡖࡤࡇࡄࡅࡔࡈࡗࡘࡥࡕࡏࡔࡈࡅࡈࡎࡁࡃࡎࡈࠫᨗ"),
  bstack1111ll_opy_ (u"ࠩࡈࡖࡗࡥࡔࡖࡐࡑࡉࡑࡥࡃࡐࡐࡑࡉࡈ࡚ࡉࡐࡐࡢࡊࡆࡏࡌࡆࡆᨘࠪ"),
  bstack1111ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡄࡑࡑࡒࡊࡉࡔࡊࡑࡑࡣ࡙ࡏࡍࡆࡆࡢࡓ࡚࡚ࠧᨙ"),
  bstack1111ll_opy_ (u"ࠫࡊࡘࡒࡠࡕࡒࡇࡐ࡙࡟ࡄࡑࡑࡒࡊࡉࡔࡊࡑࡑࡣࡋࡇࡉࡍࡇࡇࠫᨚ"),
  bstack1111ll_opy_ (u"ࠬࡋࡒࡓࡡࡖࡓࡈࡑࡓࡠࡅࡒࡒࡓࡋࡃࡕࡋࡒࡒࡤࡎࡏࡔࡖࡢ࡙ࡓࡘࡅࡂࡅࡋࡅࡇࡒࡅࠨᨛ"),
  bstack1111ll_opy_ (u"࠭ࡅࡓࡔࡢࡔࡗࡕࡘ࡚ࡡࡆࡓࡓࡔࡅࡄࡖࡌࡓࡓࡥࡆࡂࡋࡏࡉࡉ࠭᨜"),
  bstack1111ll_opy_ (u"ࠧࡆࡔࡕࡣࡓࡇࡍࡆࡡࡑࡓ࡙ࡥࡒࡆࡕࡒࡐ࡛ࡋࡄࠨ᨝"),
  bstack1111ll_opy_ (u"ࠨࡇࡕࡖࡤࡔࡁࡎࡇࡢࡖࡊ࡙ࡏࡍࡗࡗࡍࡔࡔ࡟ࡇࡃࡌࡐࡊࡊࠧ᨞"),
  bstack1111ll_opy_ (u"ࠩࡈࡖࡗࡥࡍࡂࡐࡇࡅ࡙ࡕࡒ࡚ࡡࡓࡖࡔ࡞࡙ࡠࡅࡒࡒࡋࡏࡇࡖࡔࡄࡘࡎࡕࡎࡠࡈࡄࡍࡑࡋࡄࠨ᨟"),
]
bstack1l111l111_opy_ = bstack1111ll_opy_ (u"ࠪ࠲࠴ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠱ࡦࡸࡴࡪࡨࡤࡧࡹࡹ࠯ࠨᨠ")
bstack1lll11ll11_opy_ = os.path.join(os.path.expanduser(bstack1111ll_opy_ (u"ࠫࢃ࠭ᨡ")), bstack1111ll_opy_ (u"ࠬ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠬᨢ"), bstack1111ll_opy_ (u"࠭࠮ࡣࡵࡷࡥࡨࡱ࠭ࡤࡱࡱࡪ࡮࡭࠮࡫ࡵࡲࡲࠬᨣ"))
bstack11ll1ll1111_opy_ = bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡀ࠯࠰ࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰ࠳ࡦࡶࡩࠨᨤ")
bstack11l1l1ll1l1_opy_ = [ bstack1111ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࠨᨥ"), bstack1111ll_opy_ (u"ࠩࡵࡳࡧࡵࡴࠨᨦ"), bstack1111ll_opy_ (u"ࠪࡴࡦࡨ࡯ࡵࠩᨧ"), bstack1111ll_opy_ (u"ࠫࡧ࡫ࡨࡢࡸࡨࠫᨨ")]
bstack11lll1111l_opy_ = [ bstack1111ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬᨩ"), bstack1111ll_opy_ (u"࠭ࡲࡰࡤࡲࡸࠬᨪ"), bstack1111ll_opy_ (u"ࠧࡱࡣࡥࡳࡹ࠭ᨫ"), bstack1111ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥࠨᨬ") ]
bstack1l1l1l11_opy_ = [ bstack1111ll_opy_ (u"ࠩࡵࡳࡧࡵࡴࠨᨭ") ]
bstack11l1l1l1l11_opy_ = [ bstack1111ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪᨮ") ]
bstack1llll11ll1_opy_ = 360
bstack11ll1111l1l_opy_ = bstack1111ll_opy_ (u"ࠦࡦࡶࡰ࠮ࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰࠦᨯ")
bstack11l1ll1l111_opy_ = bstack1111ll_opy_ (u"ࠧࡧࡵࡵࡱࡰࡥࡹ࡫࠯ࡢࡲ࡬࠳ࡻ࠷࠯ࡪࡵࡶࡹࡪࡹࠢᨰ")
bstack11l1ll1111l_opy_ = bstack1111ll_opy_ (u"ࠨࡡࡶࡶࡲࡱࡦࡺࡥ࠰ࡣࡳ࡭࠴ࡼ࠱࠰࡫ࡶࡷࡺ࡫ࡳ࠮ࡵࡸࡱࡲࡧࡲࡺࠤᨱ")
bstack11ll1ll1l1l_opy_ = bstack1111ll_opy_ (u"ࠢࡂࡲࡳࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠡࡶࡨࡷࡹࡹࠠࡢࡴࡨࠤࡸࡻࡰࡱࡱࡵࡸࡪࡪࠠࡰࡰࠣࡓࡘࠦࡶࡦࡴࡶ࡭ࡴࡴࠠࠦࡵࠣࡥࡳࡪࠠࡢࡤࡲࡺࡪࠦࡦࡰࡴࠣࡅࡳࡪࡲࡰ࡫ࡧࠤࡩ࡫ࡶࡪࡥࡨࡷ࠳ࠨᨲ")
bstack11ll11l1ll1_opy_ = bstack1111ll_opy_ (u"ࠣ࠳࠴࠲࠵ࠨᨳ")
bstack111l1l11ll_opy_ = {
  bstack1111ll_opy_ (u"ࠩࡓࡅࡘ࡙ࠧᨴ"): bstack1111ll_opy_ (u"ࠪࡴࡦࡹࡳࡦࡦࠪᨵ"),
  bstack1111ll_opy_ (u"ࠫࡋࡇࡉࡍࠩᨶ"): bstack1111ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬᨷ"),
  bstack1111ll_opy_ (u"࠭ࡓࡌࡋࡓࠫᨸ"): bstack1111ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨᨹ")
}
bstack1111ll11_opy_ = [
  bstack1111ll_opy_ (u"ࠣࡩࡨࡸࠧᨺ"),
  bstack1111ll_opy_ (u"ࠤࡪࡳࡇࡧࡣ࡬ࠤᨻ"),
  bstack1111ll_opy_ (u"ࠥ࡫ࡴࡌ࡯ࡳࡹࡤࡶࡩࠨᨼ"),
  bstack1111ll_opy_ (u"ࠦࡷ࡫ࡦࡳࡧࡶ࡬ࠧᨽ"),
  bstack1111ll_opy_ (u"ࠧࡩ࡬ࡪࡥ࡮ࡉࡱ࡫࡭ࡦࡰࡷࠦᨾ"),
  bstack1111ll_opy_ (u"ࠨࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࠥᨿ"),
  bstack1111ll_opy_ (u"ࠢࡴࡷࡥࡱ࡮ࡺࡅ࡭ࡧࡰࡩࡳࡺࠢᩀ"),
  bstack1111ll_opy_ (u"ࠣࡵࡨࡲࡩࡑࡥࡺࡵࡗࡳࡊࡲࡥ࡮ࡧࡱࡸࠧᩁ"),
  bstack1111ll_opy_ (u"ࠤࡶࡩࡳࡪࡋࡦࡻࡶࡘࡴࡇࡣࡵ࡫ࡹࡩࡊࡲࡥ࡮ࡧࡱࡸࠧᩂ"),
  bstack1111ll_opy_ (u"ࠥࡧࡱ࡫ࡡࡳࡇ࡯ࡩࡲ࡫࡮ࡵࠤᩃ"),
  bstack1111ll_opy_ (u"ࠦࡦࡩࡴࡪࡱࡱࡷࠧᩄ"),
  bstack1111ll_opy_ (u"ࠧ࡫ࡸࡦࡥࡸࡸࡪ࡙ࡣࡳ࡫ࡳࡸࠧᩅ"),
  bstack1111ll_opy_ (u"ࠨࡥࡹࡧࡦࡹࡹ࡫ࡁࡴࡻࡱࡧࡘࡩࡲࡪࡲࡷࠦᩆ"),
  bstack1111ll_opy_ (u"ࠢࡤ࡮ࡲࡷࡪࠨᩇ"),
  bstack1111ll_opy_ (u"ࠣࡳࡸ࡭ࡹࠨᩈ"),
  bstack1111ll_opy_ (u"ࠤࡳࡩࡷ࡬࡯ࡳ࡯ࡗࡳࡺࡩࡨࡂࡥࡷ࡭ࡴࡴࠢᩉ"),
  bstack1111ll_opy_ (u"ࠥࡴࡪࡸࡦࡰࡴࡰࡑࡺࡲࡴࡪࡖࡲࡹࡨ࡮ࠢᩊ"),
  bstack1111ll_opy_ (u"ࠦࡸ࡮ࡡ࡬ࡧࠥᩋ"),
  bstack1111ll_opy_ (u"ࠧࡩ࡬ࡰࡵࡨࡅࡵࡶࠢᩌ")
]
bstack11l1ll11l11_opy_ = [
  bstack1111ll_opy_ (u"ࠨࡣ࡭࡫ࡦ࡯ࠧᩍ"),
  bstack1111ll_opy_ (u"ࠢࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࠦᩎ"),
  bstack1111ll_opy_ (u"ࠣࡣࡸࡸࡴࠨᩏ"),
  bstack1111ll_opy_ (u"ࠤࡰࡥࡳࡻࡡ࡭ࠤᩐ"),
  bstack1111ll_opy_ (u"ࠥࡸࡪࡹࡴࡤࡣࡶࡩࠧᩑ")
]
bstack1l11ll111_opy_ = {
  bstack1111ll_opy_ (u"ࠦࡨࡲࡩࡤ࡭ࠥᩒ"): [bstack1111ll_opy_ (u"ࠧࡩ࡬ࡪࡥ࡮ࡉࡱ࡫࡭ࡦࡰࡷࠦᩓ")],
  bstack1111ll_opy_ (u"ࠨࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࠥᩔ"): [bstack1111ll_opy_ (u"ࠢࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࠦᩕ")],
  bstack1111ll_opy_ (u"ࠣࡣࡸࡸࡴࠨᩖ"): [bstack1111ll_opy_ (u"ࠤࡶࡩࡳࡪࡋࡦࡻࡶࡘࡴࡋ࡬ࡦ࡯ࡨࡲࡹࠨᩗ"), bstack1111ll_opy_ (u"ࠥࡷࡪࡴࡤࡌࡧࡼࡷ࡙ࡵࡁࡤࡶ࡬ࡺࡪࡋ࡬ࡦ࡯ࡨࡲࡹࠨᩘ"), bstack1111ll_opy_ (u"ࠦࡸࡩࡲࡦࡧࡱࡷ࡭ࡵࡴࠣᩙ"), bstack1111ll_opy_ (u"ࠧࡩ࡬ࡪࡥ࡮ࡉࡱ࡫࡭ࡦࡰࡷࠦᩚ")],
  bstack1111ll_opy_ (u"ࠨ࡭ࡢࡰࡸࡥࡱࠨᩛ"): [bstack1111ll_opy_ (u"ࠢ࡮ࡣࡱࡹࡦࡲࠢᩜ")],
  bstack1111ll_opy_ (u"ࠣࡶࡨࡷࡹࡩࡡࡴࡧࠥᩝ"): [bstack1111ll_opy_ (u"ࠤࡷࡩࡸࡺࡣࡢࡵࡨࠦᩞ")],
}
bstack11l1ll11111_opy_ = {
  bstack1111ll_opy_ (u"ࠥࡧࡱ࡯ࡣ࡬ࡇ࡯ࡩࡲ࡫࡮ࡵࠤ᩟"): bstack1111ll_opy_ (u"ࠦࡨࡲࡩࡤ࡭᩠ࠥ"),
  bstack1111ll_opy_ (u"ࠧࡹࡣࡳࡧࡨࡲࡸ࡮࡯ࡵࠤᩡ"): bstack1111ll_opy_ (u"ࠨࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࠥᩢ"),
  bstack1111ll_opy_ (u"ࠢࡴࡧࡱࡨࡐ࡫ࡹࡴࡖࡲࡉࡱ࡫࡭ࡦࡰࡷࠦᩣ"): bstack1111ll_opy_ (u"ࠣࡵࡨࡲࡩࡑࡥࡺࡵࠥᩤ"),
  bstack1111ll_opy_ (u"ࠤࡶࡩࡳࡪࡋࡦࡻࡶࡘࡴࡇࡣࡵ࡫ࡹࡩࡊࡲࡥ࡮ࡧࡱࡸࠧᩥ"): bstack1111ll_opy_ (u"ࠥࡷࡪࡴࡤࡌࡧࡼࡷࠧᩦ"),
  bstack1111ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡥࡤࡷࡪࠨᩧ"): bstack1111ll_opy_ (u"ࠧࡺࡥࡴࡶࡦࡥࡸ࡫ࠢᩨ")
}
bstack111l11ll1l_opy_ = {
  bstack1111ll_opy_ (u"࠭ࡂࡆࡈࡒࡖࡊࡥࡁࡍࡎࠪᩩ"): bstack1111ll_opy_ (u"ࠧࡔࡷ࡬ࡸࡪࠦࡓࡦࡶࡸࡴࠬᩪ"),
  bstack1111ll_opy_ (u"ࠨࡃࡉࡘࡊࡘ࡟ࡂࡎࡏࠫᩫ"): bstack1111ll_opy_ (u"ࠩࡖࡹ࡮ࡺࡥࠡࡖࡨࡥࡷࡪ࡯ࡸࡰࠪᩬ"),
  bstack1111ll_opy_ (u"ࠪࡆࡊࡌࡏࡓࡇࡢࡉࡆࡉࡈࠨᩭ"): bstack1111ll_opy_ (u"࡙ࠫ࡫ࡳࡵࠢࡖࡩࡹࡻࡰࠨᩮ"),
  bstack1111ll_opy_ (u"ࠬࡇࡆࡕࡇࡕࡣࡊࡇࡃࡉࠩᩯ"): bstack1111ll_opy_ (u"࠭ࡔࡦࡵࡷࠤ࡙࡫ࡡࡳࡦࡲࡻࡳ࠭ᩰ")
}
bstack11l1ll111l1_opy_ = 65536
bstack11l1ll1ll1l_opy_ = bstack1111ll_opy_ (u"ࠧ࠯࠰࠱࡟࡙ࡘࡕࡏࡅࡄࡘࡊࡊ࡝ࠨᩱ")
bstack11l1ll11ll1_opy_ = [
      bstack1111ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪᩲ"), bstack1111ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬᩳ"), bstack1111ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡑࡴࡲࡼࡾ࠭ᩴ"), bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨ᩵"), bstack1111ll_opy_ (u"ࠬࡩࡵࡴࡶࡲࡱ࡛ࡧࡲࡪࡣࡥࡰࡪࡹࠧ᩶"),
      bstack1111ll_opy_ (u"࠭ࡰࡳࡱࡻࡽ࡚ࡹࡥࡳࠩ᩷"), bstack1111ll_opy_ (u"ࠧࡱࡴࡲࡼࡾࡖࡡࡴࡵࠪ᩸"), bstack1111ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡐࡳࡱࡻࡽ࡚ࡹࡥࡳࠩ᩹"), bstack1111ll_opy_ (u"ࠩ࡯ࡳࡨࡧ࡬ࡑࡴࡲࡼࡾࡖࡡࡴࡵࠪ᩺"),
      bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡸࡷࡪࡸࡎࡢ࡯ࡨࠫ᩻"), bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵࡎࡩࡾ࠭᩼"), bstack1111ll_opy_ (u"ࠬࡧࡵࡵࡪࡗࡳࡰ࡫࡮ࠨ᩽")
    ]
bstack11l1l1ll11l_opy_= {
  bstack1111ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪ᩾"): bstack1111ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯᩿ࠫ"),
  bstack1111ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࡌࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷࠬ᪀"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࡍࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭᪁"),
  bstack1111ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᪂"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡘࡺࡡࡤ࡭ࡏࡳࡨࡧ࡬ࡐࡲࡷ࡭ࡴࡴࡳࠨ᪃"),
  bstack1111ll_opy_ (u"ࠬࡶࡡࡳࡣ࡯ࡰࡪࡲࡳࡑࡧࡵࡔࡱࡧࡴࡧࡱࡵࡱࠬ᪄"): bstack1111ll_opy_ (u"࠭ࡰࡢࡴࡤࡰࡱ࡫࡬ࡴࡒࡨࡶࡕࡲࡡࡵࡨࡲࡶࡲ࠭᪅"),
  bstack1111ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪ᪆"): bstack1111ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ᪇"),
  bstack1111ll_opy_ (u"ࠩ࡯ࡳ࡬ࡒࡥࡷࡧ࡯ࠫ᪈"): bstack1111ll_opy_ (u"ࠪࡰࡴ࡭ࡌࡦࡸࡨࡰࠬ᪉"),
  bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡒࡵࡳࡽࡿࠧ᪊"): bstack1111ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡓࡶࡴࡾࡹࠨ᪋"),
  bstack1111ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࡕࡸ࡯ࡹࡻࠪ᪌"): bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼࠫ᪍"),
  bstack1111ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠫ᪎"): bstack1111ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬ᪏"),
  bstack1111ll_opy_ (u"ࠪࡸࡪࡹࡴࡄࡱࡱࡸࡪࡾࡴࡐࡲࡷ࡭ࡴࡴࡳࠨ᪐"): bstack1111ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡅࡲࡲࡹ࡫ࡸࡵࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᪑"),
  bstack1111ll_opy_ (u"ࠬࡺࡥࡴࡶࡒࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࠩ᪒"): bstack1111ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪ᪓"),
  bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡗ࡫ࡰࡰࡴࡷ࡭ࡳ࡭ࠧ᪔"): bstack1111ll_opy_ (u"ࠨࡶࡨࡷࡹࡘࡥࡱࡱࡵࡸ࡮ࡴࡧࠨ᪕"),
  bstack1111ll_opy_ (u"ࠩࡷࡩࡸࡺࡏࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭᪖"): bstack1111ll_opy_ (u"ࠪࡸࡪࡹࡴࡐࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࡏࡱࡶ࡬ࡳࡳࡹࠧ᪗"),
  bstack1111ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡔࡨࡴࡴࡸࡴࡪࡰࡪࡓࡵࡺࡩࡰࡰࡶࠫ᪘"): bstack1111ll_opy_ (u"ࠬࡺࡥࡴࡶࡕࡩࡵࡵࡲࡵ࡫ࡱ࡫ࡔࡶࡴࡪࡱࡱࡷࠬ᪙"),
  bstack1111ll_opy_ (u"࠭ࡣࡶࡵࡷࡳࡲ࡜ࡡࡳ࡫ࡤࡦࡱ࡫ࡳࠨ᪚"): bstack1111ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳࡖࡢࡴ࡬ࡥࡧࡲࡥࡴࠩ᪛"),
  bstack1111ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠬ᪜"): bstack1111ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫ᪝"),
  bstack1111ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠬ᪞"): bstack1111ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳ࠭᪟"),
  bstack1111ll_opy_ (u"ࠬࡸࡥࡳࡷࡱࡘࡪࡹࡴࡴࠩ᪠"): bstack1111ll_opy_ (u"࠭ࡲࡦࡴࡸࡲ࡙࡫ࡳࡵࡵࠪ᪡"),
  bstack1111ll_opy_ (u"ࠧࡱࡧࡵࡧࡾ࠭᪢"): bstack1111ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࠧ᪣"),
  bstack1111ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࡐࡲࡷ࡭ࡴࡴࡳࠨ᪤"): bstack1111ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᪥"),
  bstack1111ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࡆࡥࡵࡺࡵࡳࡧࡐࡳࡩ࡫ࠧ᪦"): bstack1111ll_opy_ (u"ࠬࡶࡥࡳࡥࡼࡇࡦࡶࡴࡶࡴࡨࡑࡴࡪࡥࠨᪧ"),
  bstack1111ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡁࡶࡶࡲࡇࡦࡶࡴࡶࡴࡨࡐࡴ࡭ࡳࠨ᪨"): bstack1111ll_opy_ (u"ࠧࡥ࡫ࡶࡥࡧࡲࡥࡂࡷࡷࡳࡈࡧࡰࡵࡷࡵࡩࡑࡵࡧࡴࠩ᪩"),
  bstack1111ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ᪪"): bstack1111ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ᪫"),
  bstack1111ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪ᪬"): bstack1111ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶࠫ᪭"),
  bstack1111ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࠩ᪮"): bstack1111ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪ᪯"),
  bstack1111ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࡓࡵࡺࡩࡰࡰࡶࠫ᪰"): bstack1111ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࡔࡶࡴࡪࡱࡱࡷࠬ᪱"),
  bstack1111ll_opy_ (u"ࠩࡷࡩࡸࡺࡏࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳࡕࡰࡵ࡫ࡲࡲࡸ࠭᪲"): bstack1111ll_opy_ (u"ࠪࡸࡪࡹࡴࡐࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴࡏࡱࡶ࡬ࡳࡳࡹࠧ᪳"),
  bstack1111ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࡖࡩࡹࡺࡩ࡯ࡩࡶࠫ᪴"): bstack1111ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡗࡪࡺࡴࡪࡰࡪࡷ᪵ࠬ")
}
bstack11l1l1lll1l_opy_ = [bstack1111ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ᪶࠭"), bstack1111ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ᪷࠭")]
bstack1ll1l1l1l_opy_ = (bstack1111ll_opy_ (u"ࠣࡲࡼࡸࡪࡹࡴ᪸ࠣ"),)
bstack11l1l1l111l_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰ࠵ࡶ࠲࠱ࡸࡴࡩࡧࡴࡦࡡࡦࡰ࡮᪹࠭")
bstack11111ll11_opy_ = bstack1111ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴ࠼࠲࠳ࡦࡶࡩ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰ࠳ࡦࡻࡴࡰ࡯ࡤࡸࡪ࠳ࡴࡶࡴࡥࡳࡸࡩࡡ࡭ࡧ࠲ࡺ࠶࠵ࡧࡳ࡫ࡧࡷ࠴ࠨ᪺")
bstack1ll1l1111l_opy_ = bstack1111ll_opy_ (u"ࠦ࡭ࡺࡴࡱࡵ࠽࠳࠴࡭ࡲࡪࡦ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡤࡢࡵ࡫ࡦࡴࡧࡲࡥ࠱ࡥࡹ࡮ࡲࡤࡴ࠱ࠥ᪻")
bstack1ll1llll11_opy_ = bstack1111ll_opy_ (u"ࠧ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡡࡱ࡫࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡡࡶࡶࡲࡱࡦࡺࡥ࠮ࡶࡸࡶࡧࡵࡳࡤࡣ࡯ࡩ࠴ࡼ࠱࠰ࡤࡸ࡭ࡱࡪࡳ࠯࡬ࡶࡳࡳࠨ᪼")
class EVENTS(Enum):
  bstack11l1ll1ll11_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡳ࠶࠷ࡹ࠻ࡲࡵ࡭ࡳࡺ࠭ࡣࡷ࡬ࡰࡩࡲࡩ࡯࡭᪽ࠪ")
  bstack1l1ll1lll1_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡨࡲࡥࡢࡰࡸࡴࠬ᪾") # final bstack11l1lll11ll_opy_
  bstack11l1l1l1lll_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡹࡥ࡯ࡦ࡯ࡳ࡬ࡹᪿࠧ")
  bstack1llllll1ll_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡴࡶࡴࡥࡳࡸࡩࡡ࡭ࡧ࠽ࡴࡷ࡯࡮ࡵ࠯ࡥࡹ࡮ࡲࡤ࡭࡫ࡱ࡯ᫀࠬ") #shift post bstack11l1ll1lll1_opy_
  bstack1l111l1l1_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢࡷࡷࡳࡲࡧࡴࡦ࠼ࡳࡶ࡮ࡴࡴ࠮ࡤࡸ࡭ࡱࡪ࡬ࡪࡰ࡮ࠫ᫁") #shift post bstack11l1ll1lll1_opy_
  bstack11l1l1ll1ll_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡶࡨࡷࡹ࡮ࡵࡣࠩ᫂") #shift
  bstack11l1l11ll11_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡳࡩࡷࡩࡹ࠻ࡦࡲࡻࡳࡲ࡯ࡢࡦ᫃ࠪ") #shift
  bstack11ll1l1l1_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫࠺ࡩࡷࡥ࠱ࡲࡧ࡮ࡢࡩࡨࡱࡪࡴࡴࠨ᫄")
  bstack1ll11ll11l1_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦ࠷࠱ࡺ࠼ࡶࡥࡻ࡫࠭ࡳࡧࡶࡹࡱࡺࡳࠨ᫅")
  bstack1l11ll11l_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡧ࠱࠲ࡻ࠽ࡨࡷ࡯ࡶࡦࡴ࠰ࡴࡪࡸࡦࡰࡴࡰࡷࡨࡧ࡮ࠨ᫆")
  bstack11ll1ll111_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡡࡶࡶࡲࡱࡦࡺࡥ࠻࡮ࡲࡧࡦࡲࠧ᫇") #shift
  bstack1l11l1111l_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢࡲࡳ࠱ࡦࡻࡴࡰ࡯ࡤࡸࡪࡀࡡࡱࡲ࠰ࡹࡵࡲ࡯ࡢࡦࠪ᫈") #shift
  bstack1lll1lllll_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡣࡸࡸࡴࡳࡡࡵࡧ࠽ࡧ࡮࠳ࡡࡳࡶ࡬ࡪࡦࡩࡴࡴࠩ᫉")
  bstack1ll1l1l1l1_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤ࠵࠶ࡿ࠺ࡨࡧࡷ࠱ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼ࠱ࡷ࡫ࡳࡶ࡮ࡷࡷ࠲ࡹࡵ࡮࡯ࡤࡶࡾ᫊࠭") #shift
  bstack111lll1l11_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥ࠶࠷ࡹ࠻ࡩࡨࡸ࠲ࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽ࠲ࡸࡥࡴࡷ࡯ࡸࡸ࠭᫋") #shift
  bstack11l1ll111ll_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡵ࡫ࡲࡤࡻࠪᫌ") #shift
  bstack1l1l11ll1l1_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡶࡥࡳࡥࡼ࠾ࡸࡩࡲࡦࡧࡱࡷ࡭ࡵࡴࠨᫍ")
  bstack1l1111l111_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡡࡶࡶࡲࡱࡦࡺࡥ࠻ࡵࡨࡷࡸ࡯࡯࡯࠯ࡶࡸࡦࡺࡵࡴࠩᫎ") #shift
  bstack1l1l11111_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢࡷࡷࡳࡲࡧࡴࡦ࠼࡫ࡹࡧ࠳࡭ࡢࡰࡤ࡫ࡪࡳࡥ࡯ࡶࠪ᫏")
  bstack11l1l1l11ll_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡲࡵࡳࡽࡿ࠭ࡴࡧࡷࡹࡵ࠭᫐") #shift
  bstack1l1lllll_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡶࡩࡹࡻࡰࠨ᫑")
  bstack11l1ll1l1l1_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡴࡪࡸࡣࡺ࠼ࡶࡲࡦࡶࡳࡩࡱࡷࠫ᫒") # not bstack11l1ll1llll_opy_ in python
  bstack11lll1ll1_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡩࡸࡩࡷࡧࡵ࠾ࡶࡻࡩࡵࠩ᫓") # used in bstack11l1l1l1ll1_opy_
  bstack111ll111l_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡪࡲࡪࡸࡨࡶ࠿࡭ࡥࡵࠩ᫔") # used in bstack11l1l1l1ll1_opy_
  bstack1l1lll1ll_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡨࡰࡱ࡮ࠫ᫕")
  bstack1l1111ll11_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢࡷࡷࡳࡲࡧࡴࡦ࠼ࡶࡩࡸࡹࡩࡰࡰ࠰ࡲࡦࡳࡥࠨ᫖")
  bstack11lllll1_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡣࡸࡸࡴࡳࡡࡵࡧ࠽ࡷࡪࡹࡳࡪࡱࡱ࠱ࡦࡴ࡮ࡰࡶࡤࡸ࡮ࡵ࡮ࠨ᫗") #
  bstack1l1l11l11l_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡲ࠵࠶ࡿ࠺ࡥࡴ࡬ࡺࡪࡸ࠭ࡵࡣ࡮ࡩࡘࡩࡲࡦࡧࡱࡗ࡭ࡵࡴࠨ᫘")
  bstack11llll1lll_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡴࡪࡸࡣࡺ࠼ࡤࡹࡹࡵ࠭ࡤࡣࡳࡸࡺࡸࡥࠨ᫙")
  bstack1l11l1lll_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡵࡸࡥ࠮ࡶࡨࡷࡹ࠭᫚")
  bstack1l1111ll1l_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡶ࡯ࡴࡶ࠰ࡸࡪࡹࡴࠨ᫛")
  bstack11l11111l1_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡤࡳ࡫ࡹࡩࡷࡀࡰࡳࡧ࠰࡭ࡳ࡯ࡴࡪࡣ࡯࡭ࡿࡧࡴࡪࡱࡱࠫ᫜") #shift
  bstack1l111l11ll_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡥࡴ࡬ࡺࡪࡸ࠺ࡱࡱࡶࡸ࠲࡯࡮ࡪࡶ࡬ࡥࡱ࡯ࡺࡢࡶ࡬ࡳࡳ࠭᫝") #shift
  bstack11l1ll1l11l_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡣࡸࡸࡴ࠳ࡣࡢࡲࡷࡹࡷ࡫ࠧ᫞")
  bstack11l1l1ll111_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤࡹࡹࡵ࡭ࡢࡶࡨ࠾࡮ࡪ࡬ࡦ࠯ࡷ࡭ࡲ࡫࡯ࡶࡶࠪ᫟")
  bstack1lll11llll1_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡧࡱ࡯࠺ࡴࡶࡤࡶࡹ࠭᫠")
  bstack11l1l11lll1_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡨࡲࡩ࠻ࡦࡲࡻࡳࡲ࡯ࡢࡦࠪ᫡")
  bstack11l1lll11l1_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡩ࡬ࡪ࠼ࡦ࡬ࡪࡩ࡫࠮ࡷࡳࡨࡦࡺࡥࠨ᫢")
  bstack1lll11ll1ll_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡣ࡭࡫࠽ࡳࡳ࠳ࡢࡰࡱࡷࡷࡹࡸࡡࡱࠩ᫣")
  bstack1lll1lll1ll_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡤ࡮࡬࠾ࡴࡴ࠭ࡤࡱࡱࡲࡪࡩࡴࠨ᫤")
  bstack1ll1l11llll_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡥ࡯࡭࠿ࡵ࡮࠮ࡵࡷࡳࡵ࠭᫥")
  bstack1ll1ll11111_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡶࡸࡦࡸࡴࡃ࡫ࡱࡗࡪࡹࡳࡪࡱࡱࠫ᫦")
  bstack1ll1lll11l1_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡧࡴࡴ࡮ࡦࡥࡷࡆ࡮ࡴࡓࡦࡵࡶ࡭ࡴࡴࠧ᫧")
  bstack11l1l1lllll_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡩࡸࡩࡷࡧࡵࡍࡳ࡯ࡴࠨ᫨")
  bstack11l1l1llll1_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿࡬ࡩ࡯ࡦࡑࡩࡦࡸࡥࡴࡶࡋࡹࡧ࠭᫩")
  bstack1l11l1ll111_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࡉࡶࡦࡳࡥࡸࡱࡵ࡯ࡎࡴࡩࡵࠩ᫪")
  bstack1l11l1l11l1_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡊࡷࡧ࡭ࡦࡹࡲࡶࡰ࡙ࡴࡢࡴࡷࠫ᫫")
  bstack1ll11ll1111_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡄࡱࡱࡪ࡮࡭ࠧ᫬")
  bstack11l1l1lll11_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡲࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࡅࡲࡲ࡫࡯ࡧࠨ᫭")
  bstack1l1llll1ll1_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥ࡮࡙ࡥ࡭ࡨࡋࡩࡦࡲࡓࡵࡧࡳࠫ᫮")
  bstack1l1llllll11_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦ࡯ࡓࡦ࡮ࡩࡌࡪࡧ࡬ࡈࡧࡷࡖࡪࡹࡵ࡭ࡶࠪ᫯")
  bstack1l1l1l1l11l_opy_ = bstack1111ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡺࡥࡴࡶࡉࡶࡦࡳࡥࡸࡱࡵ࡯ࡊࡼࡥ࡯ࡶࠪ᫰")
  bstack1l1ll111l1l_opy_ = bstack1111ll_opy_ (u"ࠩࡶࡨࡰࡀࡴࡦࡵࡷࡗࡪࡹࡳࡪࡱࡱࡉࡻ࡫࡮ࡵࠩ᫱")
  bstack1l1l1l1ll11_opy_ = bstack1111ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡤ࡮࡬࠾ࡱࡵࡧࡄࡴࡨࡥࡹ࡫ࡤࡆࡸࡨࡲࡹ࠭᫲")
  bstack11l1lll111l_opy_ = bstack1111ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡥ࡯࡭࠿࡫࡮ࡲࡷࡨࡹࡪ࡚ࡥࡴࡶࡈࡺࡪࡴࡴࠨ᫳")
  bstack1l11l1l1l11_opy_ = bstack1111ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡌࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡔࡶࡲࡴࠬ᫴")
  bstack1lll1ll1111_opy_ = bstack1111ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡳࡳ࡙ࡴࡰࡲࠪ᫵")
class STAGE(Enum):
  bstack1l11l1l11_opy_ = bstack1111ll_opy_ (u"ࠧࡴࡶࡤࡶࡹ࠭᫶")
  END = bstack1111ll_opy_ (u"ࠨࡧࡱࡨࠬ᫷")
  bstack11ll1ll1ll_opy_ = bstack1111ll_opy_ (u"ࠩࡶ࡭ࡳ࡭࡬ࡦࠩ᫸")
bstack111111ll_opy_ = {
  bstack1111ll_opy_ (u"ࠪࡔ࡞࡚ࡅࡔࡖࠪ᫹"): bstack1111ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫ᫺"),
  bstack1111ll_opy_ (u"ࠬࡖ࡙ࡕࡇࡖࡘ࠲ࡈࡄࡅࠩ᫻"): bstack1111ll_opy_ (u"࠭ࡐࡺࡶࡨࡷࡹ࠳ࡣࡶࡥࡸࡱࡧ࡫ࡲࠨ᫼")
}
PLAYWRIGHT_HUB_URL = bstack1111ll_opy_ (u"ࠢࡸࡵࡶ࠾࠴࠵ࡣࡥࡲ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࡂࡧࡦࡶࡳ࠾ࠤ᫽")
bstack1ll11l1l1l1_opy_ = 98
bstack1ll1l111111_opy_ = 100
bstack11111lll1l_opy_ = {
  bstack1111ll_opy_ (u"ࠨࡴࡨࡶࡺࡴࠧ᫾"): bstack1111ll_opy_ (u"ࠩ࠰࠱ࡷ࡫ࡲࡶࡰࡶࠫ᫿"),
  bstack1111ll_opy_ (u"ࠪࡨࡪࡲࡡࡺࠩᬀ"): bstack1111ll_opy_ (u"ࠫ࠲࠳ࡲࡦࡴࡸࡲࡸ࠳ࡤࡦ࡮ࡤࡽࠬᬁ"),
  bstack1111ll_opy_ (u"ࠬࡸࡥࡳࡷࡱ࠱ࡩ࡫࡬ࡢࡻࠪᬂ"): 0
}
bstack11l1l1l1111_opy_ = bstack1111ll_opy_ (u"ࠨࡨࡵࡶࡳࡷ࠿࠵࠯ࡤࡱ࡯ࡰࡪࡩࡴࡰࡴ࠰ࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲࠨᬃ")
bstack11l1l1l1l1l_opy_ = bstack1111ll_opy_ (u"ࠢࡩࡶࡷࡴࡸࡀ࠯࠰ࡷࡳࡰࡴࡧࡤ࠮ࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰࠦᬄ")
bstack1l11l11l_opy_ = bstack1111ll_opy_ (u"ࠣࡖࡈࡗ࡙ࠦࡒࡆࡒࡒࡖ࡙ࡏࡎࡈࠢࡄࡒࡉࠦࡁࡏࡃࡏ࡝࡙ࡏࡃࡔࠤᬅ")