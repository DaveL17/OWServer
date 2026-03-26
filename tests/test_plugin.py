"""

"""
import dotenv
import os
from tests.shared import APIBase # noqa
from tests.shared.utils import run_host_script
import textwrap

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


# ===================================== simpleeval.py =====================================
class TestSimpleEval(APIBase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_something(self):
        pass
