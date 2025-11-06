import importlib
import sys
from pathlib import Path

def hot_reload_module_from_cwd(module_name: str):
    """
    Import or reload a Python module from the CWD.

    This function performs a "hot reload" of a module — reloading it to apply any
    recently saved code changes without restarting the kernel or Python interpreter.
    It ensures that the current working directory is included in `sys.path`, removes
    a `.py` suffix from the module name if present, and uses Python's `importlib`
    utilities to import or reload the module as appropriate.

    Args:
        module_name (str): The name of the module to import or reload.
            Can be specified either as:
            - a plain module name (e.g., 'my_module')
            - or a filename ending in '.py' (e.g., 'my_module.py')

    Returns:
        module: The imported or reloaded Python module object.

    Example:
        >>> mod = hot_reload_module_from_cwd("my_module")
        >>> mod = hot_reload_module_from_cwd("my_module.py")
    """

    # Remove '.py' suffix if the module name is given as a filename
    if module_name.endswith('.py'):
        module_name = Path(module_name).stem

    # Ensure current working directory is in sys.path
    cwd = Path.cwd().as_posix()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # Import or reload
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    else:
        return importlib.import_module(module_name)
