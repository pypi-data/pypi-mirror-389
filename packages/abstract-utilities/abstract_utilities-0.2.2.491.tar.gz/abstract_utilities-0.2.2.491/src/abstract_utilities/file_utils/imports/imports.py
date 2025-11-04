# ============================================================
# abstract_utilities/imports/imports.py
# Global imports hub — everything imported here will be
# automatically available to any module that does:
#     from ..imports import *
# ============================================================


import os
import sys, importlib,os
import sys, importlib, os, inspect
from pathlib import Path
import os,sys



from typing import *
import re

from typing import *
from types import MethodType
import os,re, sys, importlib, inspect, os, importlib.util, hashlib
import os,tempfile,shutil,logging,ezodf,fnmatch,pytesseract,pdfplumber
import pandas as pd
import geopandas as gpd
from datetime import datetime

from typing import *
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from pdf2image import convert_from_path   # only used for OCR fallback
# ---- Core standard library modules -------------------------
import os, sys, re, shlex, glob, platform, textwrap, subprocess, inspect, json, time
import tempfile, shutil, logging, pathlib, fnmatch, importlib, importlib.util, types

from datetime import datetime
from types import ModuleType

# ---- Dataclasses and typing --------------------------------
from dataclasses import dataclass, field
from typing import (
    Any, Optional, List, Dict, Set, Tuple,
    Iterable, Callable, Literal, Union, TypeVar
)

# ---- Common 3rd-party dependencies --------------------------
import pandas as pd
import geopandas as gpd
import pytesseract
import pdfplumber
import PyPDF2
import ezodf
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# ---- Helpers ------------------------------------------------
import textwrap as tw
from pprint import pprint

# ============================================================
# AUTO-EXPORT ALL NON-PRIVATE NAMES
# ============================================================
__all__ = [name for name in globals() if not name.startswith("_")]

