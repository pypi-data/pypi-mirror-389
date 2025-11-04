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
from browserstack_sdk.bstack1l11ll1l1_opy_ import bstack1lll1ll1ll_opy_
from browserstack_sdk.bstack1111lll111_opy_ import RobotHandler
def bstack1111lll1_opy_(framework):
    if framework.lower() == bstack1111ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧᬮ"):
        return bstack1lll1ll1ll_opy_.version()
    elif framework.lower() == bstack1111ll_opy_ (u"ࠨࡴࡲࡦࡴࡺࠧᬯ"):
        return RobotHandler.version()
    elif framework.lower() == bstack1111ll_opy_ (u"ࠩࡥࡩ࡭ࡧࡶࡦࠩᬰ"):
        import behave
        return behave.__version__
    else:
        return bstack1111ll_opy_ (u"ࠪࡹࡳࡱ࡮ࡰࡹࡱࠫᬱ")
def bstack11llll11l1_opy_():
    import importlib.metadata
    framework_name = []
    framework_version = []
    try:
        from selenium import webdriver
        framework_name.append(bstack1111ll_opy_ (u"ࠫࡸ࡫࡬ࡦࡰ࡬ࡹࡲ࠭ᬲ"))
        framework_version.append(importlib.metadata.version(bstack1111ll_opy_ (u"ࠧࡹࡥ࡭ࡧࡱ࡭ࡺࡳࠢᬳ")))
    except:
        pass
    try:
        import playwright
        framework_name.append(bstack1111ll_opy_ (u"࠭ࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶ᬴ࠪ"))
        framework_version.append(importlib.metadata.version(bstack1111ll_opy_ (u"ࠢࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠦᬵ")))
    except:
        pass
    return {
        bstack1111ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭ᬶ"): bstack1111ll_opy_ (u"ࠩࡢࠫᬷ").join(framework_name),
        bstack1111ll_opy_ (u"ࠪࡺࡪࡸࡳࡪࡱࡱࠫᬸ"): bstack1111ll_opy_ (u"ࠫࡤ࠭ᬹ").join(framework_version)
    }