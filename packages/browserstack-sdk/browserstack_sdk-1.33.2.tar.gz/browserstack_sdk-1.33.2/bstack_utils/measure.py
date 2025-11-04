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
import logging
from functools import wraps
from typing import Optional
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.bstack1lll1llll1_opy_ import get_logger
from bstack_utils.bstack11lll111l_opy_ import bstack1ll1lllll1l_opy_
bstack11lll111l_opy_ = bstack1ll1lllll1l_opy_()
logger = get_logger(__name__)
def measure(event_name: EVENTS, stage: STAGE, hook_type: Optional[str] = None, bstack1l1l1l1ll1_opy_: Optional[str] = None):
    bstack1111ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࡄࡦࡥࡲࡶࡦࡺ࡯ࡳࠢࡷࡳࠥࡲ࡯ࡨࠢࡷ࡬ࡪࠦࡳࡵࡣࡵࡸࠥࡺࡩ࡮ࡧࠣࡳ࡫ࠦࡡࠡࡨࡸࡲࡨࡺࡩࡰࡰࠣࡩࡽ࡫ࡣࡶࡶ࡬ࡳࡳࠐࠠࠡࠢࠣࡥࡱࡵ࡮ࡨࠢࡺ࡭ࡹ࡮ࠠࡦࡸࡨࡲࡹࠦ࡮ࡢ࡯ࡨࠤࡦࡴࡤࠡࡵࡷࡥ࡬࡫࠮ࠋࠢࠣࠤࠥࠨࠢࠣḡ")
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            label: str = event_name.value
            bstack1ll1111l1l1_opy_: str = bstack11lll111l_opy_.bstack11ll111llll_opy_(label)
            start_mark: str = label + bstack1111ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺࠢḢ")
            end_mark: str = label + bstack1111ll_opy_ (u"ࠣ࠼ࡨࡲࡩࠨḣ")
            result = None
            try:
                if stage.value == STAGE.bstack1l11l1l11_opy_.value:
                    bstack11lll111l_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                elif stage.value == STAGE.END.value:
                    result = func(*args, **kwargs)
                    bstack11lll111l_opy_.end(label, start_mark, end_mark, status=True, failure=None,hook_type=hook_type,test_name=bstack1l1l1l1ll1_opy_)
                elif stage.value == STAGE.bstack11ll1ll1ll_opy_.value:
                    start_mark: str = bstack1ll1111l1l1_opy_ + bstack1111ll_opy_ (u"ࠤ࠽ࡷࡹࡧࡲࡵࠤḤ")
                    end_mark: str = bstack1ll1111l1l1_opy_ + bstack1111ll_opy_ (u"ࠥ࠾ࡪࡴࡤࠣḥ")
                    bstack11lll111l_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                    bstack11lll111l_opy_.end(label, start_mark, end_mark, status=True, failure=None, hook_type=hook_type,test_name=bstack1l1l1l1ll1_opy_)
            except Exception as e:
                bstack11lll111l_opy_.end(label, start_mark, end_mark, status=False, failure=str(e), hook_type=hook_type,
                                       test_name=bstack1l1l1l1ll1_opy_)
            return result
        return wrapper
    return decorator