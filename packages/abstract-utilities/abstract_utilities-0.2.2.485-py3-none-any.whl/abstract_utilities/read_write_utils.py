"""
read_write_utils.py
-------------------
Unified read/write utility for safe file operations.
Supports:
- Writing content to a file
- Reading content from a file
- Creating and reading if missing
- Detecting file/content params via positional args or kwargs

Usage:
    from abstract_utilities.read_write_utils import *
"""

import os
import shlex
from .ssh_utils.utils import run_cmd,get_print_sudo_cmd,run_local_cmd,run_remote_cmd
from .file_utils.file_utils.type_checks import is_file,is_dir,get_user_pass_host_key,is_exists
from .abstract_classes import run_pruned_func
_FILE_PATH_KEYS = ['file', 'filepath', 'file_path', 'path', 'directory', 'f', 'dst', 'dest']
_CONTENTS_KEYS = ['cont', 'content', 'contents', 'data', 'datas', 'dat', 'src', 'source']

            
# --- Helper utilities --------------------------------------------------------
def string_in_keys(strings, kwargs):
    """Find a matching keyword in kwargs that contains any of the given substrings."""
    for key in kwargs:
        for s in strings:
            if s.lower() in key.lower():
                return key
    return None

def make_dirs(path,exist_ok=True,**kwargs):
    if exist_ok or (not exist_ok and not is_dir(path,**kwargs)):
        if get_user_pass_host_key(**kwargs):
            kwargs['cmd']=f"mkdir {path}"
            run_pruned_func(run_cmd,**kwargs)
        else:
            os.makedirs(path,exist_ok=exist_ok)
    return path
def path_join(*args):
    path = None
    for i,arg in enumerate(args):
        if arg:
            if i == 0:
                path = arg
            else:
                path = os.path.join(path,arg)
    return path
def make_path(path,home_dir=None,file=None,**kwargs):
    if path:
        basename = os.path.basename(path)
        parts = path.split('/')
        parts = [part for part in parts if part]
        
        full_dir = home_dir or ''
        if file == True or (file == None and ('.' in basename)):
            pieces = parts[:-1] if len(parts) > 1 else []
        else:
            pieces=parts
            basename=None
        for piece in pieces:
            full_dir = os.path.join(full_dir,piece)
            make_dirs(full_dir,exist_ok=True,**kwargs)
        if basename:
            full_dir=path_join(full_dir,basename)
        print(f"full_dir == {full_dir}")
        return full_dir
def get_path(paths,**kwargs):
    """Return the first valid path among given paths."""
    for path in paths:
        if isinstance(path, str):
            if is_file(path,**kwargs):
                return path
            dirname = os.path.dirname(path)
            if is_exists(dirname,**kwargs):
                return path
    return None


def break_down_find_existing(path,**kwargs):
    """Return the first non-existent subpath within a path chain."""
    test_path = ''
    for part in path.split(os.sep):
        test_path = os.path.join(test_path, part)
        if not is_exists(test_path,**kwargs):
            return test_path if test_path else None
    return test_path


# --- Parameter parsing --------------------------------------------------------
def check_read_write_params(*args, **kwargs):
    """
    Determine file_path and contents from arguments.
    Returns a tuple: (file_path, contents)
    """
    file_key = string_in_keys(_FILE_PATH_KEYS, kwargs)
    content_key = string_in_keys(_CONTENTS_KEYS, kwargs)

    file_path = kwargs.get(file_key) if file_key else None
    contents = kwargs.get(content_key) if content_key else None

    # Handle positional args (fallback)
    if file_path is None and len(args) > 0:
        file_path = args[0]
    if contents is None and len(args) > 1:
        contents = args[1]

    if file_path is None:
        raise ValueError("Missing file_path argument.")
    return file_path, contents

def write_to_path(
        file_path: str,
        contents: str,
        *,
        user_at_host: str = None,
        cwd: str | None = None,
        password=None,
        key=None,
        env_path=None,
        **kwargs
    ) -> str:
    """
    Completely overwrite a file (locally or remotely).
    Supports sudo and password-based remote execution.
    """

    # sanitize for shell safety
    quoted_path = shlex.quote(file_path)
    quoted_data = shlex.quote(str(contents))

    # shell command that fully overwrites
    # (no append, replaces contents entirely)
    base_cmd = f'sudo sh -c "echo {quoted_data} > {quoted_path}"'
    input(base_cmd)
    # optional sudo password injection
    full_cmd = get_print_sudo_cmd(
        cmd=base_cmd,
        password=password,
        key=key,
        env_path=env_path
    )

    # local or remote dispatch
    if user_at_host:
        return run_remote_cmd(
            user_at_host=user_at_host,
            cmd=full_cmd,
            cwd=cwd,
            password=password,
            key=key,
            env_path=env_path,
            **kwargs
        )
    else:
        return run_local_cmd(
            cmd=full_cmd,
            cwd=cwd,
            password=password,
            key=key,
            env_path=env_path,
            **kwargs
        )
### --- Core functionality -------------------------------------------------------
##def write_to_file(*args, **kwargs):
##    """
##    Write contents to a file (create if missing).
##
##    Returns the file_path written.
##    """
##    file_path, contents = check_read_write_params(*args, **kwargs)
##    if contents is None:
##        raise ValueError("Missing contents to write.")
##
##    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
##    with open(file_path, "w", encoding="utf-8") as f:
##        f.write(str(contents))
##    return file_path
# --- Core functionality -------------------------------------------------------
def write_to_file(*args, **kwargs):
    """
    Write contents to a file (create if missing).

    Returns the file_path written.
    """
    file_path, contents = check_read_write_params(*args, **kwargs)
    dirname = os.path.dirname(file_path)
    
    if contents is None:
        raise ValueError("Missing contents to write.")
    user_at_host = kwargs.get("user_at_host")
    if get_user_pass_host_key(**kwargs):
        make_dirs(dirname, exist_ok=True,**kwargs)
        kwargs["cwd"] = kwargs.get('cwd') or os.path.dirname(file_path)
        # sanitize for shell safety
        quoted_path = shlex.quote(file_path)
        quoted_data = shlex.quote(str(contents))
        # shell command that fully overwrites
        # (no append, replaces contents entirely)
        kwargs["cmd"] = f'sh -c "echo {quoted_data} > {quoted_path}"'
        if not kwargs.get('password') and not kwargs.get('key'):
            kwargs["cmd"]=f'sudo {kwargs["cmd"]}'
        result = run_pruned_func(run_cmd,**kwargs)
        if not is_file(file_path,**kwargs) or str(contents) != read_from_file(file_path,**kwargs):
            kwargs["cmd"]=f'sudo {kwargs["cmd"]}'
            result = run_pruned_func(run_cmd,**kwargs)
        return result

    make_dirs(dirname or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(contents))
    return file_path


def read_from_file(file_path,**kwargs):
    if get_user_pass_host_key(**kwargs):
        kwargs["cwd"] = kwargs.get('cwd') or os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        kwargs["cmd"] = f'cat {basename}'
        return run_pruned_func(run_cmd,**kwargs)
    """Read text content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
def get_rel_path(src,src_rel,directory):
    if src.startswith(src_rel):
        src = src[len(src_rel):]
        rel_path = os.path.join(directory,src)
        return rel_path
def make_relative_path(src,src_rel,dst,**kwargs):
    print(f"src == {src}\nsrc_rel == {src_rel}\dst == {dst}")
    if src.startswith(src_rel):
        rel_path = get_rel_path(src,src_rel,dst)
        path = make_path(src,home_dir=rel_path,**kwargs)
        print(f"path == {path}")
        return path
def copy_dirs(dirs,dst,src_rel=None,**kwargs):
    for src in dirs:
        if rel_path:
            dst = make_relative_path(src,src_rel,dst,**kwargs)
        make_path(dst,**kwargs)
        
def copy_file(src,dst,rel_path=None,**kwargs):
    if rel_path:
        dst = make_relative_path(src,rel_path,dst,**kwargs)
    if get_user_pass_host_key(**kwargs):
        contents=read_from_file(src,**kwargs)
        write_to_file(contents=contents,file_path=dst,**kwargs)
    else:
        shutil.copy(src,dst)
    return dst
def copy_files(files,dst,rel_path=None,**kwargs):
    for file in files:
        copy_file(src=file,dst=dst,rel_path=rel_path,**kwargs)

def create_and_read_file(*args, **kwargs):
    """
    Create the file (if missing) and read contents from it.
    """
    file_path, contents = check_read_write_params(*args, **kwargs)
    if not os.path.isfile(file_path):
        write_to_file(file_path, contents or "")
    return read_from_file(file_path)


def is_file_extension(obj: str) -> bool:
    """Return True if obj looks like a filename with extension."""
    if not isinstance(obj, str):
        return False
    root, ext = os.path.splitext(obj)
    return bool(root and ext)


def delete_file(file_path: str):
    """Safely delete a file if it exists."""
    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False


def get_content_lines(*args, **kwargs):
    """Return a list of lines from string or file path."""
    file_path, contents = check_read_write_params(*args, **kwargs)
    if os.path.isfile(file_path):
        contents = read_from_file(filepath)

    if isinstance(contents, str):
        return contents.splitlines()
    elif isinstance(contents, list):
        return contents
    return []
