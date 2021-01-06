# pkg_list
collects meta info of files and folders under a given directory for verify / comparing later ...

notice! only tested on linux.
# example `pkg_list.txt`

```python
d 777 work work . - -
f 777 work work constants.py - 2eb8e25a5588ca968bc5d7ef7d0439f25b253db8
f 777 work work proactor_events.py - 9ce01887f75bdf369dc35d6fb1535537e4b1c578
f 777 work work README.txt - b73a4e56e950f224ced5c14554004ee8827ceb22
d 777 work work subdir1 - -
f 777 work work subdir1/staggered.py - 5b467453e8ca8c71074625a946a290789aff861a
f 777 work work subdir1/streams.py - 43ad3429a1ad0f600146308b58c304a889387445
```
fields explained:

- file type
    - `d` for directory
    - `l` for symbolic link
    - `f` for regular file
- permission
- owner 
- group
- relative path (relative to base path)
- link to (path) or `-`
- sha1 hash or `-` for directory / symbolic link

external symbolic link is not allowed and will cause exception thrown while generating pkg_list.txt file.

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