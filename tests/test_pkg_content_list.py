from tests.base_ut import CaseWithTestFolder
from pkg_list.pkg_content_list import PkgContentList
from pkg_list import pkg_content_list as pcl
import os
import unittest


class TestPkgContentList(CaseWithTestFolder):
    def test_gen_pkg_list_file(self):
        """测试 pkg_list.txt 文件可正常生成"""
        # 准备
        pkg_file_path, t_dir = self.prepare()

        # 生成
        pcl.gen_pkg_list_file(t_dir)

        # 验证
        self.assertTrue(os.path.exists(pkg_file_path))
        with open(pkg_file_path, "r") as f:
            for line in f:
                print(line.rstrip('\n'))

    def test_verify_dir_success(self):
        """测试目录校验通过

        """
        #  准备
        pkg_file_path, t_dir = self.prepare()

        # 生成
        pcl.gen_pkg_list_file(t_dir)

        # 校验
        pcl.verify_dir(t_dir)

    def verify_dir_failed_template(self, file_modify_fun):
        """文件缺失的情况，verify 失败"""
        #  准备
        pkg_file_path, t_dir = self.prepare()
        one_txt = os.path.join(t_dir, "1.txt")
        with open(one_txt, "w") as f:
            """覆写测试文件"""
            f.write("asdgf")

        # 生成
        pcl.gen_pkg_list_file(t_dir)

        # 对文件做一些操作
        file_modify_fun(one_txt)

        # 校验（失败）
        ok, msg, passed_count, failed_count = pcl.verify_dir(t_dir)
        # fail
        self.assertFalse(ok)
        # one fail count
        self.assertEqual(1, failed_count)
        # extra debug info
        import logging
        logging.error(msg)
        logging.error("verify statistics. [passed_count=%r, failed_count=%r]" % (passed_count, failed_count))

    def test_verify_dir_failed_missing_file(self):
        """缺文件，校验失败"""

        def del_file(file_path):
            os.remove(file_path)

        self.verify_dir_failed_template(del_file)

    def test_verify_dir_failed_file_changed(self):
        """文件变更，校验失败"""

        def modify_file(file_path):
            with open(file_path, 'w') as f:
                f.write("qwertyu")

        self.verify_dir_failed_template(modify_file)

    def test_verify_dir_failed_not_pkg_file(self):
        """没有 pkg_list.txt 文件，所以校验失败"""

        # 准备
        pkg_file_path, t_dir = self.prepare()
        one_txt = os.path.join(t_dir, "1.txt")

        if os.path.exists(pkg_file_path):
            os.remove(pkg_file_path)

        # 校验（失败）
        ok, msg, passed_count, failed_count = pcl.verify_dir(t_dir)
        # fail
        self.assertFalse(ok)
        import logging
        logging.error(msg)

    @unittest.skip(reason="尚未实现这种校验，以后实现了要加上")
    def test_verify_dir_failed_add_extra_file(self):
        """多了额外的文件，校验失败"""
        # TODO 待实现
        pass

    def prepare(self):
        # 准备
        t_dir = self.res_dir("test_pkg_content_list")
        pkg_file_path = os.path.join(t_dir, PkgContentList.PKG_LIST_FILE_NAME)
        if os.path.exists(pkg_file_path):
            os.remove(pkg_file_path)
        return pkg_file_path, t_dir
