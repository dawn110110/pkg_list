# encoding=utf-8
"""对文件的元数据操作进行轻度的专用封装.
"""
import os
import pathlib
import shlex

__all__ = ['FsObjectMeta']


class FsObjectMeta:
    """自己的文件（也包括目录和符号链接）元数据类. 提供元数据的序列化输出、反序列化、校验等.

    有如下可用属性：

    type: 文件类型  d 为目录，f 为文件，l 为符号链接
    perm_mask: 权限 例如 555 777 600
    owner: 所有者用户名，例如 work 在 windows 系统上 build 时默认取 work
    group: 所属组名，例如 work 在 windows 系统 build 时默认取 work
    rel_path: 相对路径，相对于 base_path，总是以 posix 分隔符的风格表示（即使在 windows 上）
    link_to: 如果是符号链接，则取 readlink 值，否则为 None
    sha1_hash: 如果是真实文件，则取 hex(sha1(file_stream))，否则为 None


    TODO 性能优化，跑的比较慢.
    """
    FMT_STR = "{type} {perm} {owner} {group} {rel_path} {link_to} {hash}"
    FMT_STR_ELEMENTS_COUNT = 7  # fmt str 的元素个数

    def __init__(self, path=None, base_path=None, desc_str=None, nt_default_owner=None, nt_default_group=None):
        if path is None and desc_str is None:
            raise Exception("path and desc str, must choose at least one.")
        if base_path is None:
            raise Exception("base_base is always required.")

        self.path = None
        self.base_path = None

        self.type = None
        self.perm_mask = None
        self.owner = None
        self.group = None
        self.rel_path = None
        self.link_to = None
        self.sha1_hash = None

        self.nt_default_owner = nt_default_owner or 'work'
        self.nt_default_group = nt_default_group or 'work'

        if path:
            self.init_from_real_file(base_path, path)
        if desc_str:
            self.init_from_meta_desc_str(base_path, desc_str)

    def init_from_real_file(self, base_path, path):
        """从本地的真实文件初始化"""
        self.base_path = os.path.normpath(base_path)
        self.path = os.path.normpath(path)
        if not os.path.exists(path):
            raise Exception(
                "file not exists, could not init fs meta object, this may be a bug. [path=%r]" % path)
        if os.path.islink(path):
            self.type = 'l'
        elif os.path.isdir(path):
            self.type = 'd'
        elif os.path.isfile(path):
            self.type = 'f'
        else:
            raise Exception(
                "no other types supported. accepted types: symbolic link, directory, regular file. [path=%r]" % path)
        self.perm_mask = self.get_perm_mask(path)
        self.owner = self.get_owner_user(path)
        self.group = self.get_group(path)
        self.rel_path = self.path_to_posix_style(os.path.relpath(self.path, self.base_path))
        if os.path.islink(path):
            self.link_to = os.path.relpath(os.readlink(path), start=self.base_path)
        else:
            self.link_to = None
        if not os.path.islink(path) and os.path.isfile(path):
            from pkg_list.hash_util import sha1_hex
            self.sha1_hash = sha1_hex(path)
        else:
            self.sha1_hash = None

    @staticmethod
    def file_size_in_bytes(path):
        """in bytes"""
        return os.stat(path).st_size

    @staticmethod
    def path_to_posix_style(rel_path):
        """only accept relative path"""
        p = pathlib.PurePath(rel_path)
        return p.as_posix()

    @staticmethod
    def get_perm_mask(path):
        """get "777 555 600" style oct permission description string"""
        import os
        return oct(os.stat(path).st_mode & 0o777)[2:]

    def get_owner_user(self, path):
        """owner name"""
        if os.name == 'nt':
            return self.nt_default_owner
        else:
            from pwd import getpwuid
            return getpwuid(os.stat(path).st_uid).pw_name

    def get_group(self, path):
        """group name"""
        if os.name == 'nt':
            return self.nt_default_group
        else:
            from grp import getgrgid
            return getgrgid(os.stat(path).st_gid).gr_name

    @staticmethod
    def from_path(path, base_path):
        return FsObjectMeta(path, base_path)

    def to_str(self):
        _link_to = self.link_to or '-'
        _hash = self.sha1_hash or '-'
        import shlex
        var_dict = dict(
            type=shlex.quote(self.type),
            perm=self.perm_mask,
            owner=self.owner,
            group=self.group,
            rel_path=self.rel_path,
            link_to=_link_to,
            hash=_hash)
        # 使用 shell 的 quote 处理空格等情况
        var_dict_quoted = {k: self.shell_quote(var_dict[k]) for k in var_dict}
        return self.FMT_STR.format(**var_dict_quoted)

    def to_str_for_human(self, style=None):
        """
        Args:
            style (): 可选：prettytable stringio 默认优先 prettytable 没安装则使用 stringio

        Returns:

        """
        """转化为对人类阅读友好的格式"""
        use_style = 'stringio'
        try:
            import prettytable
            has_pretty_table = True
        except:
            has_pretty_table = False

        file_type_map = {
            'f': 'normal file',
            'd': 'directory',
            'l': 'symbolic link'
        }
        if style == 'prettytable':
            if not has_pretty_table:
                raise Exception("install pretty table first before use it's style.")
            else:
                use_style = 'prettytable'
        if style == 'stringio':
            use_style = 'stringio'

        if use_style == 'prettytable':
            """使用 pretty table 打表格"""

            t = prettytable.PrettyTable(["key", "value"])
            t.align = 'l'
            t.add_row(['object_type', self.type + " (" + file_type_map.get(self.type) + ')'])
            t.add_row(['permission', self.perm_mask])
            t.add_row(['owner', self.owner])
            t.add_row(['group', self.group])
            t.add_row(['base_path', self.base_path])
            t.add_row(['rel_path', self.rel_path or '-'])
            t.add_row(['link_to', self.link_to or '-'])
            t.add_row(['sha1_hash', self.sha1_hash])
            return t.get_string()
        else:
            from io import StringIO
            sio = StringIO()

            print(' '.join(['object_type', self.type + " (" + file_type_map.get(self.type) + ')']), file=sio)
            out_parts = [
                ['object_type :', self.type + " (" + file_type_map.get(self.type) or '' + ')'],
                ['permission  :', self.perm_mask or ''],
                ['owner       :', self.owner or ''],
                ['group       :', self.group or ''],
                ['base_path   :', self.base_path or ''],
                ['rel_path    :', self.rel_path or '-'],
                ['link_to     :', self.link_to or '-'],
                ['sha1_hash   :', self.sha1_hash or ''], ]
            for parts in out_parts:
                line_str = ' '.join(parts).rstrip('\n')
                print(line_str, file=sio)
            return sio.getvalue()

    @staticmethod
    def shell_quote(src: str):
        return shlex.quote(src)

    @staticmethod
    def shell_unquote(src: str):
        """基本是 shlex.quote 的逆方法. 请参见其源码."""
        if src.startswith("'") and src.endswith("'"):
            return src[1:-1].replace("'\"'\"'", "'")
        else:
            return src

    def init_from_meta_desc_str(self, base_path, desc_str: str):
        self.base_path = os.path.normpath(base_path)
        self.path = os.path.normpath(base_path)

        _desc_str = desc_str.rstrip('\n').rstrip().lstrip().rstrip('\n').rstrip()  # 简单去除一些开头末尾的空格\n
        sp = shlex.split(desc_str)
        if len(sp) != self.FMT_STR_ELEMENTS_COUNT:
            raise Exception(
                "invalid fs object meta desc string, wrong elements count."
                " [expected_count=%r, real_count=%r, desc_str=%r]" % (
                    self.FMT_STR_ELEMENTS_COUNT,
                    len(sp),
                    _desc_str))
        self.type = sp[0]
        self.perm_mask = sp[1]
        self.owner = sp[2]
        self.group = sp[3]
        self.rel_path = self.shell_unquote(sp[4])
        self.link_to = self.shell_unquote(sp[5])
        self.sha1_hash = sp[6]

    def verify(self, target_path: str = None):
        """检查当前 descriptor 的定义，是否与给定文件的 path 一致.

        Args:
            target_path (): 需要比较的文件/目录的路径，相对于当前工作目录的路径（而非 self.base_path），
                            可以不传不传则按当前 desc_str 中的描述查找

        Returns: 四元组，(是否匹配，可读的不匹配原因说明，理想描述串，真实描述串)

        """
        if target_path:
            _target_path = target_path
        else:
            _target_path = os.path.join(self.base_path, self.rel_path)
        my_str = self.to_str()
        if not os.path.exists(_target_path):
            msg = 'file not exists'
            return False, msg, my_str, None
        target_file_descriptor = FsObjectMeta(base_path=self.base_path, path=_target_path)
        your_str = target_file_descriptor.to_str()
        matched = my_str == your_str
        if matched:
            msg = ''
        else:
            msg = 'file meta not match'

        return matched, msg, my_str, your_str
