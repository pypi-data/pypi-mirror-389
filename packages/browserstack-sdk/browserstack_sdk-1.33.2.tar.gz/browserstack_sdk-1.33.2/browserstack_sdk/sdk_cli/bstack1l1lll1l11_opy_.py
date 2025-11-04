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
from collections import defaultdict
from threading import Lock
from dataclasses import dataclass
import logging
import traceback
from typing import List, Dict, Any
import os
@dataclass
class bstack11lll1lll1_opy_:
    sdk_version: str
    path_config: str
    path_project: str
    test_framework: str
    frameworks: List[str]
    framework_versions: Dict[str, str]
    bs_config: Dict[str, Any]
@dataclass
class bstack11lll1ll1l_opy_:
    pass
class bstack11llll111_opy_:
    bstack1ll1ll111_opy_ = bstack1111ll_opy_ (u"ࠥࡦࡴࡵࡴࡴࡶࡵࡥࡵࠨᆃ")
    CONNECT = bstack1111ll_opy_ (u"ࠦࡨࡵ࡮࡯ࡧࡦࡸࠧᆄ")
    bstack111lllll1_opy_ = bstack1111ll_opy_ (u"ࠧࡹࡨࡶࡶࡧࡳࡼࡴࠢᆅ")
    CONFIG = bstack1111ll_opy_ (u"ࠨࡣࡰࡰࡩ࡭࡬ࠨᆆ")
    bstack1ll1l111l1l_opy_ = bstack1111ll_opy_ (u"ࠢࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡶࠦᆇ")
    bstack1l11ll1111_opy_ = bstack1111ll_opy_ (u"ࠣࡧࡻ࡭ࡹࠨᆈ")
class bstack1ll1l111ll1_opy_:
    bstack1ll1l11l111_opy_ = bstack1111ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡵࡷࡥࡷࡺࡥࡥࠤᆉ")
    FINISHED = bstack1111ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡩ࡭ࡳ࡯ࡳࡩࡧࡧࠦᆊ")
class bstack1ll1l1111l1_opy_:
    bstack1ll1l11l111_opy_ = bstack1111ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡳࡵࡣࡵࡸࡪࡪࠢᆋ")
    FINISHED = bstack1111ll_opy_ (u"ࠧࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡧ࡫ࡱ࡭ࡸ࡮ࡥࡥࠤᆌ")
class bstack1ll1l1111ll_opy_:
    bstack1ll1l11l111_opy_ = bstack1111ll_opy_ (u"ࠨࡨࡰࡱ࡮ࡣࡷࡻ࡮ࡠࡵࡷࡥࡷࡺࡥࡥࠤᆍ")
    FINISHED = bstack1111ll_opy_ (u"ࠢࡩࡱࡲ࡯ࡤࡸࡵ࡯ࡡࡩ࡭ࡳ࡯ࡳࡩࡧࡧࠦᆎ")
class bstack1ll1l111l11_opy_:
    bstack1ll1l11l11l_opy_ = bstack1111ll_opy_ (u"ࠣࡥࡥࡸࡤࡹࡥࡴࡵ࡬ࡳࡳࡥࡣࡳࡧࡤࡸࡪࡪࠢᆏ")
class bstack1ll1l111lll_opy_:
    _1ll1ll1l1ll_opy_ = None
    def __new__(cls):
        if not cls._1ll1ll1l1ll_opy_:
            cls._1ll1ll1l1ll_opy_ = super(bstack1ll1l111lll_opy_, cls).__new__(cls)
        return cls._1ll1ll1l1ll_opy_
    def __init__(self):
        self._hooks = defaultdict(lambda: defaultdict(list))
        self._lock = Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
    def clear(self):
        with self._lock:
            self._hooks = defaultdict(list)
    def register(self, event_name, callback):
        with self._lock:
            if not callable(callback):
                raise ValueError(bstack1111ll_opy_ (u"ࠤࡆࡥࡱࡲࡢࡢࡥ࡮ࠤࡲࡻࡳࡵࠢࡥࡩࠥࡩࡡ࡭࡮ࡤࡦࡱ࡫ࠠࡧࡱࡵࠤࠧᆐ") + event_name)
            pid = os.getpid()
            self.logger.debug(bstack1111ll_opy_ (u"ࠥࡖࡪ࡭ࡩࡴࡶࡨࡶ࡮ࡴࡧࠡࡥࡤࡰࡱࡨࡡࡤ࡭ࠣࡪࡴࡸࠠࡦࡸࡨࡲࡹࠦࠧࡼࡧࡹࡩࡳࡺ࡟࡯ࡣࡰࡩࢂ࠭ࠠࡸ࡫ࡷ࡬ࠥࡶࡩࡥࠢࠥᆑ") + str(pid) + bstack1111ll_opy_ (u"ࠦࠧᆒ"))
            self._hooks[event_name][pid].append(callback)
    def invoke(self, event_name, *args, **kwargs):
        with self._lock:
            pid = os.getpid()
            callbacks = self._hooks.get(event_name, {}).get(pid, [])
            if not callbacks:
                self.logger.warning(bstack1111ll_opy_ (u"ࠧࡔ࡯ࠡࡥࡤࡰࡱࡨࡡࡤ࡭ࡶࠤ࡫ࡵࡲࠡࡧࡹࡩࡳࡺࠠࠨࡽࡨࡺࡪࡴࡴࡠࡰࡤࡱࡪࢃࠧࠡࡹ࡬ࡸ࡭ࠦࡰࡪࡦࠣࠦᆓ") + str(pid) + bstack1111ll_opy_ (u"ࠨࠢᆔ"))
                return
            self.logger.debug(bstack1111ll_opy_ (u"ࠢࡊࡰࡹࡳࡰ࡯࡮ࡨࠢࡾࡰࡪࡴࠨࡤࡣ࡯ࡰࡧࡧࡣ࡬ࡵࠬࢁࠥࡩࡡ࡭࡮ࡥࡥࡨࡱࡳࠡࡨࡲࡶࠥ࡫ࡶࡦࡰࡷࠤࠬࢁࡥࡷࡧࡱࡸࡤࡴࡡ࡮ࡧࢀࠫࠥࡽࡩࡵࡪࠣࡴ࡮ࡪࠠࠣᆕ") + str(pid) + bstack1111ll_opy_ (u"ࠣࠤᆖ"))
            for callback in callbacks:
                try:
                    self.logger.debug(bstack1111ll_opy_ (u"ࠤࡌࡲࡻࡵ࡫ࡦࡦࠣࡧࡦࡲ࡬ࡣࡣࡦ࡯ࠥ࡬࡯ࡳࠢࡨࡺࡪࡴࡴࠡࠩࡾࡩࡻ࡫࡮ࡵࡡࡱࡥࡲ࡫ࡽࠨࠢࡺ࡭ࡹ࡮ࠠࡱ࡫ࡧࠤࠧᆗ") + str(pid) + bstack1111ll_opy_ (u"ࠥࠦᆘ"))
                    callback(event_name, *args, **kwargs)
                except Exception as e:
                    self.logger.error(bstack1111ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣ࡭ࡳࡼ࡯࡬࡫ࡱ࡫ࠥࡩࡡ࡭࡮ࡥࡥࡨࡱࠠࡧࡱࡵࠤࡪࡼࡥ࡯ࡶࠣࠫࢀ࡫ࡶࡦࡰࡷࡣࡳࡧ࡭ࡦࡿࠪࠤࡼ࡯ࡴࡩࠢࡳ࡭ࡩࠦࡻࡱ࡫ࡧࢁ࠿ࠦࠢᆙ") + str(e) + bstack1111ll_opy_ (u"ࠧࠨᆚ"))
                    traceback.print_exc()
bstack1l1lll1l11_opy_ = bstack1ll1l111lll_opy_()