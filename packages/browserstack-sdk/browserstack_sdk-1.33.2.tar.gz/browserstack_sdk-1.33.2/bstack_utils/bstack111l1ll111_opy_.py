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
from uuid import uuid4
from bstack_utils.helper import bstack1ll1l11ll1_opy_, bstack11l111ll11l_opy_
from bstack_utils.bstack1lll1ll11l_opy_ import bstack1llllll1l1l1_opy_
class bstack111l1l1l11_opy_:
    def __init__(self, name=None, code=None, uuid=None, file_path=None, started_at=None, framework=None, tags=[], scope=[], bstack1lllll11111l_opy_=None, bstack1llll1ll11l1_opy_=True, bstack1l111l1l1ll_opy_=None, bstack1lll1lll1_opy_=None, result=None, duration=None, bstack1111l1l1l1_opy_=None, meta={}):
        self.bstack1111l1l1l1_opy_ = bstack1111l1l1l1_opy_
        self.name = name
        self.code = code
        self.file_path = file_path
        self.uuid = uuid
        if not self.uuid and bstack1llll1ll11l1_opy_:
            self.uuid = uuid4().__str__()
        self.started_at = started_at
        self.framework = framework
        self.tags = tags
        self.scope = scope
        self.bstack1lllll11111l_opy_ = bstack1lllll11111l_opy_
        self.bstack1l111l1l1ll_opy_ = bstack1l111l1l1ll_opy_
        self.bstack1lll1lll1_opy_ = bstack1lll1lll1_opy_
        self.result = result
        self.duration = duration
        self.meta = meta
        self.hooks = []
    def bstack1111lllll1_opy_(self):
        if self.uuid:
            return self.uuid
        self.uuid = uuid4().__str__()
        return self.uuid
    def bstack111ll1llll_opy_(self, meta):
        self.meta = meta
    def bstack111l1llll1_opy_(self, hooks):
        self.hooks = hooks
    def bstack1llll1lll11l_opy_(self):
        bstack1llll1ll1l11_opy_ = os.path.relpath(self.file_path, start=os.getcwd())
        return {
            bstack1111ll_opy_ (u"ࠬ࡬ࡩ࡭ࡧࡢࡲࡦࡳࡥࠨ₁"): bstack1llll1ll1l11_opy_,
            bstack1111ll_opy_ (u"࠭࡬ࡰࡥࡤࡸ࡮ࡵ࡮ࠨ₂"): bstack1llll1ll1l11_opy_,
            bstack1111ll_opy_ (u"ࠧࡷࡥࡢࡪ࡮ࡲࡥࡱࡣࡷ࡬ࠬ₃"): bstack1llll1ll1l11_opy_
        }
    def set(self, **kwargs):
        for key, val in kwargs.items():
            if not hasattr(self, key):
                raise TypeError(bstack1111ll_opy_ (u"ࠣࡗࡱࡩࡽࡶࡥࡤࡶࡨࡨࠥࡧࡲࡨࡷࡰࡩࡳࡺ࠺ࠡࠤ₄") + key)
            setattr(self, key, val)
    def bstack1llll1lll1ll_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ₅"): self.name,
            bstack1111ll_opy_ (u"ࠪࡦࡴࡪࡹࠨ₆"): {
                bstack1111ll_opy_ (u"ࠫࡱࡧ࡮ࡨࠩ₇"): bstack1111ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬ₈"),
                bstack1111ll_opy_ (u"࠭ࡣࡰࡦࡨࠫ₉"): self.code
            },
            bstack1111ll_opy_ (u"ࠧࡴࡥࡲࡴࡪࡹࠧ₊"): self.scope,
            bstack1111ll_opy_ (u"ࠨࡶࡤ࡫ࡸ࠭₋"): self.tags,
            bstack1111ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬ₌"): self.framework,
            bstack1111ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࡧࡧࡣࡦࡺࠧ₍"): self.started_at
        }
    def bstack1llll1ll1lll_opy_(self):
        return {
         bstack1111ll_opy_ (u"ࠫࡲ࡫ࡴࡢࠩ₎"): self.meta
        }
    def bstack1llll1llll1l_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠬࡩࡵࡴࡶࡲࡱࡗ࡫ࡲࡶࡰࡓࡥࡷࡧ࡭ࠨ₏"): {
                bstack1111ll_opy_ (u"࠭ࡲࡦࡴࡸࡲࡤࡴࡡ࡮ࡧࠪₐ"): self.bstack1lllll11111l_opy_
            }
        }
    def bstack1llll1ll111l_opy_(self, bstack1llll1llllll_opy_, details):
        step = next(filter(lambda st: st[bstack1111ll_opy_ (u"ࠧࡪࡦࠪₑ")] == bstack1llll1llllll_opy_, self.meta[bstack1111ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧₒ")]), None)
        step.update(details)
    def bstack11l11ll111_opy_(self, bstack1llll1llllll_opy_):
        step = next(filter(lambda st: st[bstack1111ll_opy_ (u"ࠩ࡬ࡨࠬₓ")] == bstack1llll1llllll_opy_, self.meta[bstack1111ll_opy_ (u"ࠪࡷࡹ࡫ࡰࡴࠩₔ")]), None)
        step.update({
            bstack1111ll_opy_ (u"ࠫࡸࡺࡡࡳࡶࡨࡨࡤࡧࡴࠨₕ"): bstack1ll1l11ll1_opy_()
        })
    def bstack111l1ll1ll_opy_(self, bstack1llll1llllll_opy_, result, duration=None):
        bstack1l111l1l1ll_opy_ = bstack1ll1l11ll1_opy_()
        if bstack1llll1llllll_opy_ is not None and self.meta.get(bstack1111ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫₖ")):
            step = next(filter(lambda st: st[bstack1111ll_opy_ (u"࠭ࡩࡥࠩₗ")] == bstack1llll1llllll_opy_, self.meta[bstack1111ll_opy_ (u"ࠧࡴࡶࡨࡴࡸ࠭ₘ")]), None)
            step.update({
                bstack1111ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭ₙ"): bstack1l111l1l1ll_opy_,
                bstack1111ll_opy_ (u"ࠩࡧࡹࡷࡧࡴࡪࡱࡱࠫₚ"): duration if duration else bstack11l111ll11l_opy_(step[bstack1111ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࡧࡧࡣࡦࡺࠧₛ")], bstack1l111l1l1ll_opy_),
                bstack1111ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫₜ"): result.result,
                bstack1111ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡸࡶࡪ࠭₝"): str(result.exception) if result.exception else None
            })
    def add_step(self, bstack1llll1llll11_opy_):
        if self.meta.get(bstack1111ll_opy_ (u"࠭ࡳࡵࡧࡳࡷࠬ₞")):
            self.meta[bstack1111ll_opy_ (u"ࠧࡴࡶࡨࡴࡸ࠭₟")].append(bstack1llll1llll11_opy_)
        else:
            self.meta[bstack1111ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧ₠")] = [ bstack1llll1llll11_opy_ ]
    def bstack1llll1ll1l1l_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ₡"): self.bstack1111lllll1_opy_(),
            **self.bstack1llll1lll1ll_opy_(),
            **self.bstack1llll1lll11l_opy_(),
            **self.bstack1llll1ll1lll_opy_()
        }
    def bstack1llll1ll1ll1_opy_(self):
        if not self.result:
            return {}
        data = {
            bstack1111ll_opy_ (u"ࠪࡪ࡮ࡴࡩࡴࡪࡨࡨࡤࡧࡴࠨ₢"): self.bstack1l111l1l1ll_opy_,
            bstack1111ll_opy_ (u"ࠫࡩࡻࡲࡢࡶ࡬ࡳࡳࡥࡩ࡯ࡡࡰࡷࠬ₣"): self.duration,
            bstack1111ll_opy_ (u"ࠬࡸࡥࡴࡷ࡯ࡸࠬ₤"): self.result.result
        }
        if data[bstack1111ll_opy_ (u"࠭ࡲࡦࡵࡸࡰࡹ࠭₥")] == bstack1111ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧ₦"):
            data[bstack1111ll_opy_ (u"ࠨࡨࡤ࡭ࡱࡻࡲࡦࡡࡷࡽࡵ࡫ࠧ₧")] = self.result.bstack11111111ll_opy_()
            data[bstack1111ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡵࡳࡧࠪ₨")] = [{bstack1111ll_opy_ (u"ࠪࡦࡦࡩ࡫ࡵࡴࡤࡧࡪ࠭₩"): self.result.bstack111lll11l11_opy_()}]
        return data
    def bstack1lllll111111_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠫࡺࡻࡩࡥࠩ₪"): self.bstack1111lllll1_opy_(),
            **self.bstack1llll1lll1ll_opy_(),
            **self.bstack1llll1lll11l_opy_(),
            **self.bstack1llll1ll1ll1_opy_(),
            **self.bstack1llll1ll1lll_opy_()
        }
    def bstack1111ll1l11_opy_(self, event, result=None):
        if result:
            self.result = result
        if bstack1111ll_opy_ (u"࡙ࠬࡴࡢࡴࡷࡩࡩ࠭₫") in event:
            return self.bstack1llll1ll1l1l_opy_()
        elif bstack1111ll_opy_ (u"࠭ࡆࡪࡰ࡬ࡷ࡭࡫ࡤࠨ€") in event:
            return self.bstack1lllll111111_opy_()
    def bstack1111ll1ll1_opy_(self):
        pass
    def stop(self, time=None, duration=None, result=None):
        self.bstack1l111l1l1ll_opy_ = time if time else bstack1ll1l11ll1_opy_()
        self.duration = duration if duration else bstack11l111ll11l_opy_(self.started_at, self.bstack1l111l1l1ll_opy_)
        if result:
            self.result = result
class bstack111ll1l1l1_opy_(bstack111l1l1l11_opy_):
    def __init__(self, hooks=[], bstack111ll111l1_opy_={}, *args, **kwargs):
        self.hooks = hooks
        self.bstack111ll111l1_opy_ = bstack111ll111l1_opy_
        super().__init__(*args, **kwargs, bstack1lll1lll1_opy_=bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࠬ₭"))
    @classmethod
    def bstack1llll1lll1l1_opy_(cls, scenario, feature, test, **kwargs):
        steps = []
        for step in scenario.steps:
            steps.append({
                bstack1111ll_opy_ (u"ࠨ࡫ࡧࠫ₮"): id(step),
                bstack1111ll_opy_ (u"ࠩࡷࡩࡽࡺࠧ₯"): step.name,
                bstack1111ll_opy_ (u"ࠪ࡯ࡪࡿࡷࡰࡴࡧࠫ₰"): step.keyword,
            })
        return bstack111ll1l1l1_opy_(
            **kwargs,
            meta={
                bstack1111ll_opy_ (u"ࠫ࡫࡫ࡡࡵࡷࡵࡩࠬ₱"): {
                    bstack1111ll_opy_ (u"ࠬࡴࡡ࡮ࡧࠪ₲"): feature.name,
                    bstack1111ll_opy_ (u"࠭ࡰࡢࡶ࡫ࠫ₳"): feature.filename,
                    bstack1111ll_opy_ (u"ࠧࡥࡧࡶࡧࡷ࡯ࡰࡵ࡫ࡲࡲࠬ₴"): feature.description
                },
                bstack1111ll_opy_ (u"ࠨࡵࡦࡩࡳࡧࡲࡪࡱࠪ₵"): {
                    bstack1111ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ₶"): scenario.name
                },
                bstack1111ll_opy_ (u"ࠪࡷࡹ࡫ࡰࡴࠩ₷"): steps,
                bstack1111ll_opy_ (u"ࠫࡪࡾࡡ࡮ࡲ࡯ࡩࡸ࠭₸"): bstack1llllll1l1l1_opy_(test)
            }
        )
    def bstack1llll1ll11ll_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡶࠫ₹"): self.hooks
        }
    def bstack1llll1lll111_opy_(self):
        if self.bstack111ll111l1_opy_:
            return {
                bstack1111ll_opy_ (u"࠭ࡩ࡯ࡶࡨ࡫ࡷࡧࡴࡪࡱࡱࡷࠬ₺"): self.bstack111ll111l1_opy_
            }
        return {}
    def bstack1lllll111111_opy_(self):
        return {
            **super().bstack1lllll111111_opy_(),
            **self.bstack1llll1ll11ll_opy_()
        }
    def bstack1llll1ll1l1l_opy_(self):
        return {
            **super().bstack1llll1ll1l1l_opy_(),
            **self.bstack1llll1lll111_opy_()
        }
    def bstack1111ll1ll1_opy_(self):
        return bstack1111ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࠩ₻")
class bstack111l1ll1l1_opy_(bstack111l1l1l11_opy_):
    def __init__(self, hook_type, *args,bstack111ll111l1_opy_={}, **kwargs):
        self.hook_type = hook_type
        self.bstack1ll111ll111_opy_ = None
        self.bstack111ll111l1_opy_ = bstack111ll111l1_opy_
        super().__init__(*args, **kwargs, bstack1lll1lll1_opy_=bstack1111ll_opy_ (u"ࠨࡪࡲࡳࡰ࠭₼"))
    def bstack1111lll1ll_opy_(self):
        return self.hook_type
    def bstack1llll1lllll1_opy_(self):
        return {
            bstack1111ll_opy_ (u"ࠩ࡫ࡳࡴࡱ࡟ࡵࡻࡳࡩࠬ₽"): self.hook_type
        }
    def bstack1lllll111111_opy_(self):
        return {
            **super().bstack1lllll111111_opy_(),
            **self.bstack1llll1lllll1_opy_()
        }
    def bstack1llll1ll1l1l_opy_(self):
        return {
            **super().bstack1llll1ll1l1l_opy_(),
            bstack1111ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤ࡯ࡤࠨ₾"): self.bstack1ll111ll111_opy_,
            **self.bstack1llll1lllll1_opy_()
        }
    def bstack1111ll1ll1_opy_(self):
        return bstack1111ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳ࠭₿")
    def bstack111ll11l11_opy_(self, bstack1ll111ll111_opy_):
        self.bstack1ll111ll111_opy_ = bstack1ll111ll111_opy_