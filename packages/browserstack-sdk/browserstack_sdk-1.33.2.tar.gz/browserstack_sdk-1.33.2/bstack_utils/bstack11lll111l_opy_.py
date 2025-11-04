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
from filelock import FileLock
import json
import os
import time
import uuid
import logging
from typing import Dict, List, Optional
from bstack_utils.bstack1lll1llll1_opy_ import get_logger
logger = get_logger(__name__)
bstack1lllllll1l11_opy_: Dict[str, float] = {}
bstack1lllllll1l1l_opy_: List = []
bstack1lllllllll11_opy_ = 5
bstack11ll1l1ll1_opy_ = os.path.join(os.getcwd(), bstack1111ll_opy_ (u"ࠩ࡯ࡳ࡬࠭ᾉ"), bstack1111ll_opy_ (u"ࠪ࡯ࡪࡿ࠭࡮ࡧࡷࡶ࡮ࡩࡳ࠯࡬ࡶࡳࡳ࠭ᾊ"))
logging.getLogger(bstack1111ll_opy_ (u"ࠫ࡫࡯࡬ࡦ࡮ࡲࡧࡰ࠭ᾋ")).setLevel(logging.WARNING)
lock = FileLock(bstack11ll1l1ll1_opy_+bstack1111ll_opy_ (u"ࠧ࠴࡬ࡰࡥ࡮ࠦᾌ"))
class bstack1llllllll11l_opy_:
    duration: float
    name: str
    startTime: float
    worker: int
    status: bool
    failure: str
    details: Optional[str]
    entryType: str
    platform: Optional[int]
    command: Optional[str]
    hookType: Optional[str]
    cli: Optional[bool]
    def __init__(self, duration: float, name: str, start_time: float, bstack1llllllll1ll_opy_: int, status: bool, failure: str, details: Optional[str] = None, platform: Optional[int] = None, command: Optional[str] = None, test_name: Optional[str] = None, hook_type: Optional[str] = None, cli: Optional[bool] = False) -> None:
        self.duration = duration
        self.name = name
        self.startTime = start_time
        self.worker = bstack1llllllll1ll_opy_
        self.status = status
        self.failure = failure
        self.details = details
        self.entryType = bstack1111ll_opy_ (u"ࠨ࡭ࡦࡣࡶࡹࡷ࡫ࠢᾍ")
        self.platform = platform
        self.command = command
        self.testName = test_name
        self.hookType = hook_type
        self.cli = cli
class bstack1ll1lllll1l_opy_:
    global bstack1lllllll1l11_opy_
    @staticmethod
    def bstack1ll11ll111l_opy_(key: str):
        bstack1ll1111l1l1_opy_ = bstack1ll1lllll1l_opy_.bstack11ll111llll_opy_(key)
        bstack1ll1lllll1l_opy_.mark(bstack1ll1111l1l1_opy_+bstack1111ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺࠢᾎ"))
        return bstack1ll1111l1l1_opy_
    @staticmethod
    def mark(key: str) -> None:
        try:
            bstack1lllllll1l11_opy_[key] = time.time_ns() / 1000000
        except Exception as e:
            logger.debug(bstack1111ll_opy_ (u"ࠣࡇࡵࡶࡴࡸ࠺ࠡࡽࢀࠦᾏ").format(e))
    @staticmethod
    def end(label: str, start: str, end: str, status: bool, failure: Optional[str] = None, hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            bstack1ll1lllll1l_opy_.mark(end)
            bstack1ll1lllll1l_opy_.measure(label, start, end, status, failure, hook_type, details, command, test_name)
        except Exception as e:
            logger.debug(bstack1111ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡰ࡫ࡹࠡ࡯ࡨࡸࡷ࡯ࡣࡴ࠼ࠣࡿࢂࠨᾐ").format(e))
    @staticmethod
    def measure(label: str, start: str, end: str, status: bool, failure: Optional[str], hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            if start not in bstack1lllllll1l11_opy_ or end not in bstack1lllllll1l11_opy_:
                logger.debug(bstack1111ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡹࡴࡢࡴࡷࠤࡰ࡫ࡹࠡࡹ࡬ࡸ࡭ࠦࡶࡢ࡮ࡸࡩࠥࢁࡽࠡࡱࡵࠤࡪࡴࡤࠡ࡭ࡨࡽࠥࡽࡩࡵࡪࠣࡺࡦࡲࡵࡦࠢࡾࢁࠧᾑ").format(start,end))
                return
            duration: float = bstack1lllllll1l11_opy_[end] - bstack1lllllll1l11_opy_[start]
            bstack1llllllll1l1_opy_ = os.environ.get(bstack1111ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡆࡎࡔࡁࡓ࡛ࡢࡍࡘࡥࡒࡖࡐࡑࡍࡓࡍࠢᾒ"), bstack1111ll_opy_ (u"ࠧ࡬ࡡ࡭ࡵࡨࠦᾓ")).lower() == bstack1111ll_opy_ (u"ࠨࡴࡳࡷࡨࠦᾔ")
            bstack1lllllll1ll1_opy_: bstack1llllllll11l_opy_ = bstack1llllllll11l_opy_(duration, label, bstack1lllllll1l11_opy_[start], os.getpid(), status, failure, details, os.environ.get(bstack1111ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡋࡑࡈࡊ࡞ࠢᾕ"), 0), command, test_name, hook_type, bstack1llllllll1l1_opy_)
            del bstack1lllllll1l11_opy_[start]
            del bstack1lllllll1l11_opy_[end]
            bstack1ll1lllll1l_opy_.bstack1llllllll111_opy_(bstack1lllllll1ll1_opy_)
        except Exception as e:
            logger.debug(bstack1111ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦ࡭ࡦࡣࡶࡹࡷ࡯࡮ࡨࠢ࡮ࡩࡾࠦ࡭ࡦࡶࡵ࡭ࡨࡹ࠺ࠡࡽࢀࠦᾖ").format(e))
    @staticmethod
    def bstack1llllllll111_opy_(bstack1lllllll1ll1_opy_):
        os.makedirs(os.path.dirname(bstack11ll1l1ll1_opy_)) if not os.path.exists(os.path.dirname(bstack11ll1l1ll1_opy_)) else None
        bstack1ll1lllll1l_opy_.bstack1lllllllll1l_opy_()
        try:
            with lock:
                with open(bstack11ll1l1ll1_opy_, bstack1111ll_opy_ (u"ࠤࡵ࠯ࠧᾗ"), encoding=bstack1111ll_opy_ (u"ࠥࡹࡹ࡬࠭࠹ࠤᾘ")) as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = []
                    data.append(bstack1lllllll1ll1_opy_.__dict__)
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, indent=4)
        except FileNotFoundError as bstack1lllllll1lll_opy_:
            logger.debug(bstack1111ll_opy_ (u"ࠦࡋ࡯࡬ࡦࠢࡱࡳࡹࠦࡦࡰࡷࡱࡨࠥࢁࡽࠣᾙ").format(bstack1lllllll1lll_opy_))
            with lock:
                with open(bstack11ll1l1ll1_opy_, bstack1111ll_opy_ (u"ࠧࡽࠢᾚ"), encoding=bstack1111ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧᾛ")) as file:
                    data = [bstack1lllllll1ll1_opy_.__dict__]
                    json.dump(data, file, indent=4)
        except Exception as e:
            logger.debug(bstack1111ll_opy_ (u"ࠢࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣࡻ࡭࡯࡬ࡦࠢ࡮ࡩࡾࠦ࡭ࡦࡶࡵ࡭ࡨࡹࠠࡢࡲࡳࡩࡳࡪࠠࡼࡿࠥᾜ").format(str(e)))
        finally:
            if os.path.exists(bstack11ll1l1ll1_opy_+bstack1111ll_opy_ (u"ࠣ࠰࡯ࡳࡨࡱࠢᾝ")):
                os.remove(bstack11ll1l1ll1_opy_+bstack1111ll_opy_ (u"ࠤ࠱ࡰࡴࡩ࡫ࠣᾞ"))
    @staticmethod
    def bstack1lllllllll1l_opy_():
        attempt = 0
        while (attempt < bstack1lllllllll11_opy_):
            attempt += 1
            if os.path.exists(bstack11ll1l1ll1_opy_+bstack1111ll_opy_ (u"ࠥ࠲ࡱࡵࡣ࡬ࠤᾟ")):
                time.sleep(0.5)
            else:
                break
    @staticmethod
    def bstack11ll111llll_opy_(label: str) -> str:
        try:
            return bstack1111ll_opy_ (u"ࠦࢀࢃ࠺ࡼࡿࠥᾠ").format(label,str(uuid.uuid4().hex)[:6])
        except Exception as e:
            logger.debug(bstack1111ll_opy_ (u"ࠧࡋࡲࡳࡱࡵ࠾ࠥࢁࡽࠣᾡ").format(e))