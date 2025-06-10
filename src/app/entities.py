from typing import Optional, List
from dataclasses import dataclass


@dataclass
class DebugData:

    data_in: Optional[str] = None
    code: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TestData:

    __test__ = False

    data_in: Optional[str] = None
    data_out: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    ok: Optional[bool] = None


@dataclass
class TestsData:

    __test__ = False

    tests: List[TestData]
    num: int = 0
    num_ok: int = 0
    ok: Optional[bool] = None
    code: Optional[str] = None
    checker: Optional[str] = None
