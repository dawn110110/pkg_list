from tests.base_ut import CaseWithTestFolder
from pkg_list.fs_meta import FsObjectMeta


class TestFsMeta(CaseWithTestFolder):
    """测试文件系统元数据处理"""

    def test_gen_desc_str(self):
        """测试生成文件的描述串"""
        test_base_path = self.res_dir("test_fs_meta")
        import os
        one_file = os.path.join(test_base_path, "1.txt")
        two_file = os.path.join(test_base_path, "2.txt")

        one_handle = FsObjectMeta(base_path=test_base_path, path=one_file)
        desc_str = one_handle.to_str()
        print(desc_str)
        print(one_handle.to_str_for_human())
        # expect no exception

    def test_process_symlink_and_reverse_parse(self):
        """正确处理一层符号链接，以及反序列化"""
        # 准备符号链接
        test_base_path = self.res_dir("test_fs_meta")
        import os
        one_file = os.path.join(test_base_path, "1.txt")
        one_symlink = os.path.join(test_base_path, "1_link.txt")
        if not os.path.exists(one_symlink):
            os.symlink(one_file, one_symlink)

        # 处理符号链接
        one_link_handle = FsObjectMeta(base_path=test_base_path, path=one_symlink)
        desc_str = one_link_handle.to_str()
        print(desc_str)
        print(one_link_handle.to_str_for_human())

        # 反过来 parse desc string

        reverse_parsed = FsObjectMeta(base_path=test_base_path, desc_str=desc_str)
        to_str_again = reverse_parsed.to_str()
        self.assertEqual(desc_str, to_str_again)

    def test_symlink_tao_wa_case(self):
        """测试符号链接套娃的情况"""
        # 准备符号链接
        test_base_path = self.res_dir("test_fs_meta")
        import os

        one_file = os.path.join(test_base_path, "1.txt")
        one_link = os.path.join(test_base_path, "1_link.txt")
        if not os.path.exists(one_link):
            os.symlink(one_file, one_link)
        one_link_link = os.path.join(test_base_path, "1_link_link.txt")
        if not os.path.exists(one_link_link):
            os.symlink(one_link, one_link_link)

        # 处理 link link 文件
        ll_handle = FsObjectMeta(base_path=test_base_path, path=one_link_link)
        ll_desc = ll_handle.to_str()

        rev_parsed = FsObjectMeta(base_path=test_base_path, desc_str=ll_desc)
        self.assertEqual('l', rev_parsed.type)
        self.assertEqual('1_link.txt', rev_parsed.link_to)

    def test_process_directory(self):
        """测试处理目录，以及目录的符号链接"""

        test_base_path = self.res_dir("test_fs_meta")
        import os

        directory = os.path.join(test_base_path, "test_dir")
        dir_link = os.path.join(test_base_path, "test_dir_link")
        if not os.path.exists(dir_link):
            os.symlink(directory, dir_link)

        # 测试对目录的处理
        d_handle = FsObjectMeta(base_path=test_base_path, path=directory)
        d_link_handle = FsObjectMeta(base_path=test_base_path, path=dir_link)

        print(d_handle.to_str_for_human())
        print(d_handle.to_str())

        print(d_link_handle.to_str_for_human())
        print(d_link_handle.to_str())

        self.assertEqual('d', d_handle.type)
        self.assertEqual('l', d_link_handle.type)

        self.assertEqual(None, d_handle.link_to)
        self.assertEqual('test_dir', d_link_handle.link_to)

    def test_verify_fail(self):
        """测试 verify 失败"""
        test_base_path = self.res_dir("test_fs_meta")
        import os
        one_file = os.path.join(test_base_path, "1.txt")

        # 错误测试 ：hash 不对，校验失败
        wrong_desc_hash_1 = "f 777 work work 1.txt - 7e240xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx815"
        desc1_handle = FsObjectMeta(base_path=test_base_path, desc_str=wrong_desc_hash_1)
        check_result1, _, _, _ = desc1_handle.verify(one_file)
        self.assertEqual(False, check_result1)

        # 错误测试：格式不对，无法初始化
        wrong_desc_format_2 = "f 777 1.txt - 7e240xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx815"
        self.assertRaises(Exception, FsObjectMeta.__init__, dict(base_path=test_base_path, desc_str=wrong_desc_format_2),
                          msg="wrong format, so could not init.")

    def test_verify_success(self):
        """测试 verify 成功"""
        test_base_path = self.res_dir("test_fs_meta")
        import os
        one_file = os.path.join(test_base_path, "1.txt")

        good_desc = "f 777 work work 1.txt - 7e240de74fb1ed08fa08d38063f6a6a91462a815"
        good_desc_handle = FsObjectMeta(base_path=test_base_path, desc_str=good_desc)
        check_result, _, _, _ = good_desc_handle.verify(one_file)
        self.assertEqual(True, check_result)
