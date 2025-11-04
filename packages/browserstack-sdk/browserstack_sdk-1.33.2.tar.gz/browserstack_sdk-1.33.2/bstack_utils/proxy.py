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
from urllib.parse import urlparse
from bstack_utils.config import Config
from bstack_utils.messages import bstack111l11ll11l_opy_
bstack1l1l11ll11_opy_ = Config.bstack111l11ll1_opy_()
def bstack1lllllll111l_opy_(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
def bstack1llllll1lll1_opy_(bstack1llllll1llll_opy_, bstack1llllll1ll1l_opy_):
    from pypac import get_pac
    from pypac import PACSession
    from pypac.parser import PACFile
    import socket
    if os.path.isfile(bstack1llllll1llll_opy_):
        with open(bstack1llllll1llll_opy_) as f:
            pac = PACFile(f.read())
    elif bstack1lllllll111l_opy_(bstack1llllll1llll_opy_):
        pac = get_pac(url=bstack1llllll1llll_opy_)
    else:
        raise Exception(bstack1111ll_opy_ (u"࠭ࡐࡢࡥࠣࡪ࡮ࡲࡥࠡࡦࡲࡩࡸࠦ࡮ࡰࡶࠣࡩࡽ࡯ࡳࡵ࠼ࠣࡿࢂ࠭ᾢ").format(bstack1llllll1llll_opy_))
    session = PACSession(pac)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((bstack1111ll_opy_ (u"ࠢ࠹࠰࠻࠲࠽࠴࠸ࠣᾣ"), 80))
        bstack1lllllll1111_opy_ = s.getsockname()[0]
        s.close()
    except:
        bstack1lllllll1111_opy_ = bstack1111ll_opy_ (u"ࠨ࠲࠱࠴࠳࠶࠮࠱ࠩᾤ")
    proxy_url = session.get_pac().find_proxy_for_url(bstack1llllll1ll1l_opy_, bstack1lllllll1111_opy_)
    return proxy_url
def bstack1l11l1111_opy_(config):
    return bstack1111ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡐࡳࡱࡻࡽࠬᾥ") in config or bstack1111ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴࡒࡵࡳࡽࡿࠧᾦ") in config
def bstack1l111111ll_opy_(config):
    if not bstack1l11l1111_opy_(config):
        return
    if config.get(bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡒࡵࡳࡽࡿࠧᾧ")):
        return config.get(bstack1111ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡓࡶࡴࡾࡹࠨᾨ"))
    if config.get(bstack1111ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࡕࡸ࡯ࡹࡻࠪᾩ")):
        return config.get(bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼࠫᾪ"))
def bstack11ll11l1_opy_(config, bstack1llllll1ll1l_opy_):
    proxy = bstack1l111111ll_opy_(config)
    proxies = {}
    if config.get(bstack1111ll_opy_ (u"ࠨࡪࡷࡸࡵࡖࡲࡰࡺࡼࠫᾫ")) or config.get(bstack1111ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࡑࡴࡲࡼࡾ࠭ᾬ")):
        if proxy.endswith(bstack1111ll_opy_ (u"ࠪ࠲ࡵࡧࡣࠨᾭ")):
            proxies = bstack1ll111l1_opy_(proxy, bstack1llllll1ll1l_opy_)
        else:
            proxies = {
                bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࠪᾮ"): proxy
            }
    bstack1l1l11ll11_opy_.bstack1lll11llll_opy_(bstack1111ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡗࡪࡺࡴࡪࡰࡪࡷࠬᾯ"), proxies)
    return proxies
def bstack1ll111l1_opy_(bstack1llllll1llll_opy_, bstack1llllll1ll1l_opy_):
    proxies = {}
    global bstack1lllllll11ll_opy_
    if bstack1111ll_opy_ (u"࠭ࡐࡂࡅࡢࡔࡗࡕࡘ࡚ࠩᾰ") in globals():
        return bstack1lllllll11ll_opy_
    try:
        proxy = bstack1llllll1lll1_opy_(bstack1llllll1llll_opy_, bstack1llllll1ll1l_opy_)
        if bstack1111ll_opy_ (u"ࠢࡅࡋࡕࡉࡈ࡚ࠢᾱ") in proxy:
            proxies = {}
        elif bstack1111ll_opy_ (u"ࠣࡊࡗࡘࡕࠨᾲ") in proxy or bstack1111ll_opy_ (u"ࠤࡋࡘ࡙ࡖࡓࠣᾳ") in proxy or bstack1111ll_opy_ (u"ࠥࡗࡔࡉࡋࡔࠤᾴ") in proxy:
            bstack1lllllll11l1_opy_ = proxy.split(bstack1111ll_opy_ (u"ࠦࠥࠨ᾵"))
            if bstack1111ll_opy_ (u"ࠧࡀ࠯࠰ࠤᾶ") in bstack1111ll_opy_ (u"ࠨࠢᾷ").join(bstack1lllllll11l1_opy_[1:]):
                proxies = {
                    bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸ࠭Ᾰ"): bstack1111ll_opy_ (u"ࠣࠤᾹ").join(bstack1lllllll11l1_opy_[1:])
                }
            else:
                proxies = {
                    bstack1111ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࠨᾺ"): str(bstack1lllllll11l1_opy_[0]).lower() + bstack1111ll_opy_ (u"ࠥ࠾࠴࠵ࠢΆ") + bstack1111ll_opy_ (u"ࠦࠧᾼ").join(bstack1lllllll11l1_opy_[1:])
                }
        elif bstack1111ll_opy_ (u"ࠧࡖࡒࡐ࡚࡜ࠦ᾽") in proxy:
            bstack1lllllll11l1_opy_ = proxy.split(bstack1111ll_opy_ (u"ࠨࠠࠣι"))
            if bstack1111ll_opy_ (u"ࠢ࠻࠱࠲ࠦ᾿") in bstack1111ll_opy_ (u"ࠣࠤ῀").join(bstack1lllllll11l1_opy_[1:]):
                proxies = {
                    bstack1111ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࠨ῁"): bstack1111ll_opy_ (u"ࠥࠦῂ").join(bstack1lllllll11l1_opy_[1:])
                }
            else:
                proxies = {
                    bstack1111ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࠪῃ"): bstack1111ll_opy_ (u"ࠧ࡮ࡴࡵࡲ࠽࠳࠴ࠨῄ") + bstack1111ll_opy_ (u"ࠨࠢ῅").join(bstack1lllllll11l1_opy_[1:])
                }
        else:
            proxies = {
                bstack1111ll_opy_ (u"ࠧࡩࡶࡷࡴࡸ࠭ῆ"): proxy
            }
    except Exception as e:
        print(bstack1111ll_opy_ (u"ࠣࡵࡲࡱࡪࠦࡥࡳࡴࡲࡶࠧῇ"), bstack111l11ll11l_opy_.format(bstack1llllll1llll_opy_, str(e)))
    bstack1lllllll11ll_opy_ = proxies
    return proxies