from typing import Any, Callable, Dict, Optional, Union
from qtpy.QtWidgets import QFrame, QVBoxLayout
from qtmui.hooks import State
from ..textfield import TextField
from ..chip import Chip
class Select:
    def __init__(self, value: Optional[Union[State, Any]], onChange: Optional[Union[State, Callable]], label: Optional[Union[State, str]], fullWidth: Optional[Union[State, bool]], multiple: Optional[Union[State, bool]], defaultValue: Optional[Union[State, object]], displayEmpty: Optional[Union[State, bool]], inputProps: Optional[Union[State, Dict]], renderValue: Optional[Union[State, Callable]], getOptionLabel: Optional[Union[State, Callable]], options: Optional[Union[State, object]], open: Optional[Union[State, bool]], onOpen: Optional[Union[State, Callable]], onClose: Optional[Union[State, Callable]], defaultOpen: Optional[Union[State, bool]], disabled: Optional[Union[State, bool]], error: Optional[Union[State, bool]], renderOption: Optional[Union[State, Callable]], required: Optional[Union[State, bool]], readOnly: Optional[Union[State, bool]], sx: Optional[Union[State, Dict, Callable, str]], size: Optional[Union[State, str]], *args, **kwargs): ...
    def _init_ui(self): ...