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
import threading
import queue
from typing import Callable, Union
class bstack1llllllll11_opy_:
    timeout: int
    bstack1lllllll1ll_opy_: Union[None, Callable]
    bstack1llllllllll_opy_: Union[None, Callable]
    def __init__(self, timeout=1, bstack1lllllll1l1_opy_=1, bstack1lllllll1ll_opy_=None, bstack1llllllllll_opy_=None):
        self.timeout = timeout
        self.bstack1lllllll1l1_opy_ = bstack1lllllll1l1_opy_
        self.bstack1lllllll1ll_opy_ = bstack1lllllll1ll_opy_
        self.bstack1llllllllll_opy_ = bstack1llllllllll_opy_
        self.queue = queue.Queue()
        self.bstack1lllllllll1_opy_ = threading.Event()
        self.threads = []
    def enqueue(self, job: Callable):
        if not callable(job):
            raise ValueError(bstack1111ll_opy_ (u"ࠣ࡫ࡱࡺࡦࡲࡩࡥࠢ࡭ࡳࡧࡀࠠࠣႨ") + type(job))
        self.queue.put(job)
    def start(self):
        if self.threads:
            return
        self.threads = [threading.Thread(target=self.worker, daemon=True) for _ in range(self.bstack1lllllll1l1_opy_)]
        for thread in self.threads:
            thread.start()
    def stop(self):
        if not self.threads:
            return
        if not self.queue.empty():
            self.queue.join()
        self.bstack1lllllllll1_opy_.set()
        for _ in self.threads:
            self.queue.put(None)
        for thread in self.threads:
            thread.join()
        self.threads.clear()
    def worker(self):
        while not self.bstack1lllllllll1_opy_.is_set():
            try:
                job = self.queue.get(block=True, timeout=self.timeout)
                if job is None:
                    break
                try:
                    job()
                except Exception as e:
                    if callable(self.bstack1lllllll1ll_opy_):
                        self.bstack1lllllll1ll_opy_(e, job)
                finally:
                    self.queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                if callable(self.bstack1llllllllll_opy_):
                    self.bstack1llllllllll_opy_(e)