#encoding=utf-8
import unittest


class CaseWithTestFolder(unittest.TestCase):
    """带测试文件的 case"""

    @staticmethod
    def sh_run(cmd, **kargs):
        import subprocess as sp
        p = sp.run(cmd, capture_output=True, shell=True, **kargs)
        if p.returncode != 0:
            raise Exception("failed to run cmd, return code not zero. [cmd=%r, completed_process=%r]" % (cmd, p))
        return p.stdout.decode('utf-8').strip("\n")

    @staticmethod
    def res_dir(test_folder):
        """返回一个绝对路径，既在 .tests 包下面的 data 目录，再下一级的 {test_folder} 所处的绝对路径.

        tests/data/{test_folder}"""
        import os.path
        ret = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", test_folder))
        if ret.startswith("./"):
            raise Exception("test dir result could not starts with ./ [ret=%r]" % ret)
        else:
            return ret
