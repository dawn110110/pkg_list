# pkg_list
collects meta info of files and folders under a given directory for verify / comparing later ...

notice! only tested on linux.

# example usage

gen pkg_list.txt

```python
# generate pkg_list.txt
from pkg_list.pkg_content_list import gen_pkg_list_file

gen_pkg_list_file('./a_folder')
# cat ./a_folder/pkg_list.txt
```

verify

```python
from pkg_list.pkg_content_list import verify_dir

passed, msg, passed_count, failed_count = verify_dir('./a_folder')

print(passed)
print(msg)
print(passed_count)
print(failed_count)
```

# todo

1. setup.py and release to pypi.
2. adapt to win & macos.