import asyncio
from typing import Callable, Optional, Union, Dict, Any
from qtpy.QtGui import QPainter, QPen, QIcon
from qtpy.QtCore import Qt, QSize, Signal, QTimer, QEvent
from qtpy.QtWidgets import QAbstractButton
from ..system.color_manipulator import hex_string_to_qcolor
from qtmui.material.styles.create_theme.components.get_qss_styles import get_qss_style
from ..button.button import Button
from ..py_iconify import Iconify
from qtmui.hooks import State
from qtmui.material.styles import useTheme
from qtmui.i18n.use_translation import translate, i18n
from ..utils.functions import _get_fn_args
from ...qtmui_assets import QTMUI_ASSETS
from ..utils.validate_params import _validate_param
class Checkbox:
    def __init__(self, checked: Optional[Union[State, bool]], checkedIcon: Optional[Union[State, str, Iconify]], classes: Optional[Union[State, Dict]], color: Union[State, str], defaultChecked: Optional[Union[State, bool]], disabled: Union[State, bool], disableGutters: Union[State, bool], disableRipple: Union[State, bool], icon: Optional[Union[State, str, Iconify]], id: Optional[Union[State, str]], indeterminate: Union[State, bool], indeterminateIcon: Optional[Union[State, str, Iconify]], inputProps: Optional[Union[State, Dict]], onChange: Optional[Union[State, Callable]], required: Union[State, bool], size: Union[State, str], slotProps: Optional[Union[State, Dict]], slots: Optional[Union[State, Dict]], state: Optional[Union[State, bool]], sx: Optional[Union[State, Dict, Callable, str]], value: Optional[Union[State, Any]], *args, **kwargs): ...
    def _connectCheckboxStates(self): ...
    def _onCheckedStateChanged(self, state): ...
    def _init_ui(self): ...
    def onClick(self): ...