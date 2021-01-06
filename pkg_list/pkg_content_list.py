# encoding=utf-8
"""
处理文件内容物品列表，也叫做 “装箱单”
"""
import os
import logging
from pkg_list.fs_meta import FsObjectMeta

__all__ = ['discover_pkg_list_file', 'gen_pkg_list_file', 'verify_dir', 'PkgContentList', 'FolderFsMetaCollector']


def discover_pkg_list_file(base_path: str):
    """发现是否存在 pkg_list.txt 文件，存在则返回路径"""
    return PkgContentList.discover_pkg_list_file(base_path=base_path)


def gen_pkg_list_file(base_path: str):
    """生成 pkg list 文件，在 base_path 下"""
    pl = PkgContentList(base_path=base_path)
    pl.collect_and_check()
    pl.gen_pkg_list_file()


def verify_dir(path: str):
    """校验一个目录内容物的元数据是否与 pkg_list.txt 一致.

    1. 自动发现目录下的 pkg_list.txt 文件.
    2. 按文件中的元信息，与实际文件进行比对.
    3. 对于 pkg_list.txt 中没有提到的文件，不做校验. TODO 以后添加这个.
    4. 生成一个 pkg_list.txt.real 文件，在目录下（此文件和 plg_list.txt 在生成步骤中都会被忽略）
    5. 见 Returns

    Args:
        path (): 被检测目录

    Returns: 返回四元组 (是否校验通过，可读的提示信息，通过校验的对象个数，未通过校验的对象个数)
    """
    found_path = PkgContentList.discover_pkg_list_file(path)
    failed_list = []
    passed_count = 0
    failed_count = 0
    mentioned_rel_path = []
    if not found_path:
        msg = "could not find pkg list file under directory, could not proceed verify. [folder_path=%r]" % path
        return False, msg, passed_count, failed_count
    else:
        logging.info("discovered pkg list file. [path=%r]" % found_path)
        with open(found_path, 'r') as pkg_file:
            for line in pkg_file:
                meta = FsObjectMeta(base_path=path, desc_str=line)
                mentioned_rel_path.append(meta.rel_path)
                passed, reason_msg, expected_desc, real_desc = meta.verify()
                if not passed:
                    failed_count += 1
                    failed_list.append((reason_msg, expected_desc, real_desc))
                else:
                    passed_count += 1
        pl_real = PkgContentList(base_path=path)
        pl_real.collect_and_check(ignore_check=True)
        real_pkg_list_name = PkgContentList.PKG_LIST_FILE_NAME + ".real"
        pl_real.gen_pkg_list_file(file_name=real_pkg_list_name)
        if failed_count == 0:
            msg = "directory passed pkg list verify. [path=%r]" % path
            return True, msg, passed_count, failed_count
        else:
            msg = "directory failed on pkg list verify test, diff %s and %s under directory for detail. [path=%r]" % (
                PkgContentList.PKG_LIST_FILE_NAME,
                real_pkg_list_name,
                path)
            return False, msg, passed_count, failed_count


def path_contains(a_path, b_path):
    """判断 a_path 是否包含 b_path.

    子目录，或者实质是相同目录，都返回 True.
    不处理符号链接.
    """
    _rel_a = os.path.relpath(a_path, start='/')
    _rel_b = os.path.relpath(b_path, start='/')
    return _rel_a.startswith(_rel_b)


class FolderFsMetaCollector:
    """一个 base path 下的，文件 / 目录的 meta 信息采集器.

    最终可返回 meta str 的列表，用于进一步的装箱单生成.
    """
    collected_dict: dict[str, FsObjectMeta]

    def __init__(self, base_path: str, ignore_check=None):
        self.ignore_check = ignore_check or False
        self.base_path = base_path
        self.collected_dict = {}

    def configure_ignore_check(self, ignore: bool):
        self.ignore_check = ignore

    def get_meta_dict(self) -> dict[str, FsObjectMeta]:
        """返回 meta 对象作为 value 的字典，key 是相对于 base_path 的相对路径"""
        return self.collected_dict

    def get_desc_str_list(self) -> list[str]:
        """校验信息列表，顺序稳定，按照相对路径字典序排序"""
        collected_list: list[(str, FsObjectMeta)] = list(self.collected_dict.items())
        collected_list.sort(key=lambda x: x[0])  # 按第一个字段排序
        l: list[str] = []

        for key, meta in self.collected_dict.items():
            l.append(meta.to_str())
        return l

    def external_link_defender(self, *p):
        """外部符号链接防御"""
        if self.ignore_check:
            """如果忽略则直接返回"""
            return
        if self.is_external_link(*p):
            raise Exception(
                "external link found, it's a bad practice in packaging. [base_path=%r, bad_path=%r]" % (
                    self.base_path, os.path.normpath(os.path.join(*p))
                ))

    @staticmethod
    def is_link(*p) -> (bool, str):
        """判断是否为符号链接.

        Args:
            *p (): 一系列需要连接的目录片段

        Returns: 返回判断结果，和完整路径.
        """
        jp = os.path.join(*p)
        return os.path.islink(jp), jp

    def is_external_link(self, *p):
        """判断 link 文件是否为外部链接.

        外部，既不是 base_path 的子目录.

        Args:
            *p (): 一系列需要连接的目录片段

        Returns:

        """
        is_link_result, path = self.is_link(*p)
        return is_link_result and not path_contains(self.base_path, path)

    def norm_path(self, *p):
        """路径格式统一，转化为相对于 base_path 的相对路径，并格式归一.

        Args:
            *p (): 需要被连接到一起的一系列路径片段

        Returns: 归一后的路径，可作为字典的 key 使用

        """
        joined_p = os.path.join(*p)
        return os.path.normpath(os.path.relpath(joined_p, start=self.base_path))

    def already_collected(self, *p):
        key = self.norm_path(*p)
        return key in self.collected_dict, key

    def process_folder(self, folder_path):
        """采集 folder 信息

        Args:
            folder_path (): 既 os.walk 的 root 返回

        Returns: None

        Raises: Exception with external path found.
        """
        self.external_link_defender(folder_path)
        collected, key = self.already_collected(folder_path)
        if collected:
            return
        meta = FsObjectMeta(base_path=self.base_path, path=folder_path)
        self.collected_dict[key] = meta
        return meta

    def process_file(self, parent_folder_path, file_name):
        """采集文件信息

        Args:
            parent_folder_path ():
            file_name ():

        Returns:

        Raises: Exception with external path found.
        """
        self.external_link_defender(parent_folder_path, file_name)
        collected, key = self.already_collected(parent_folder_path, file_name)
        if collected:
            return
        path = os.path.join(parent_folder_path, file_name)
        meta = FsObjectMeta(base_path=self.base_path, path=path)
        self.collected_dict[key] = meta
        return meta


class PkgContentList:
    """装箱单的封装.

    TODO 性能优化，现在跑的比较慢.
    """

    PKG_LIST_FILE_NAME = "pkg_list.txt"

    @staticmethod
    def discover_pkg_list_file(base_path):
        """发现某个目录下的 pkg list 文件，存在则返回路径，不存在则返回 None"""
        pl_path = os.path.join(base_path, PkgContentList.PKG_LIST_FILE_NAME)
        if os.path.exists(pl_path):
            return pl_path
        else:
            return None

    def __init__(self, base_path: str):
        """初始化装箱单的封装.

        Args:
            base_path (): 基础路径
        """
        _base_path = os.path.normpath(os.path.abspath(base_path))
        self.base_path = _base_path
        self.collector = FolderFsMetaCollector(base_path=_base_path)

    def collect_and_check(self, ignore_check=None):
        """检查外部符号链接，以及采集元信息"""
        _ignore_check = ignore_check or False
        self.collector.configure_ignore_check(_ignore_check)
        for root, _, files in os.walk(self.base_path, followlinks=True):
            """不处理 dirs 返回，只管 root 和 files. 

            TODO symlink 的处理或许有待优化，不过先确保正确性."""
            self.collector.process_folder(root)
            for f in files:
                if f.startswith(self.PKG_LIST_FILE_NAME):
                    """忽略 pkg list 开头的文件"""
                    continue
                self.collector.process_file(root, f)

    def get_meta_desc_str_list(self):
        """既然生成 pkg_list.txt 的内容逐行的 list"""
        self.collector.get_desc_str_list()

    def get_meta_desc_str(self):
        """既然生成 pkg_list.txt 的内容并返回"""
        return "\n".join(self.collector.get_desc_str_list())

    def gen_pkg_list_file(self, file_name=None):
        """直接生成 pkg_list.txt 文件

        Args:
            file_name (): 非必须，不写则自动生成

        Returns: None
        """
        _file_name = file_name or self.PKG_LIST_FILE_NAME
        pkg_list_file_path = os.path.join(self.base_path, _file_name)
        with open(pkg_list_file_path, 'w') as pkg_file:
            pkg_file.write(self.get_meta_desc_str())
        import logging
        logging.info("%s file generated. [path=%r]" % (_file_name, pkg_list_file_path))
