from typing import Optional, Union, List, Dict
from dataclasses import field, replace
from functools import lru_cache

from qtpy.QtWidgets import QFrame, QVBoxLayout

from redux.main import Store

# from qtmui.hooks.use_effect import useEffect
# from qtmui.hooks import useState

from qtpy.QtWidgets import QFrame

from ...material.styles.create_theme.theme_reducer import CreateThemeAction, ChangePaletteAction, MergeOverideComponentsAction, ThemeState

from .root_reducer import root_reducer, StateType, ActionType


from qtpy.QtCore import QObject, Property, Signal

from qtmui.utils.lodash import merge

from ..system import (
    hexToRgb,
    rgbToHex,
    hslToRgb,
    decomposeColor,
    recomposeColor,
    getContrastRatio,
    getLuminance,
    emphasize,
    alpha,
    darken,
    lighten,
)

from .styled import styled

class ThemeSignal(QObject):
    changed = Signal()

    def __init__(self, theme=None):
        super().__init__()
        self._theme = theme

    def getTheme(self) -> dict:
        return self._theme

    def setTheme(self, value):
        if self._theme != value:
            self._theme = value
            self.changed.emit()

    theme = Property(str, getTheme, setTheme, notify=changed)

themeSignal = ThemeSignal()

def onThemeChanged(data: dict):
    themeSignal.theme = data
    

theme_store: Store[StateType, ActionType, None] = Store(root_reducer)
theme_store.dispatch(CreateThemeAction())


def setTheme(mode):
    theme_store.dispatch(ChangePaletteAction(mode=mode))
    onThemeChanged(theme_store._state.theme)

# @lru_cache(maxsize=128) ===> lỗi 

def useTheme():
    theme: ThemeState = theme_store._state.theme
    theme = replace(theme, signal=themeSignal)
    return theme



class ThemeProvider(QFrame):
    def __init__(
        self, 
        children: Optional[List],
        theme: Optional[Dict]
    ):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        self._children = children
        
        themeSignal.changed.connect(self.initUi)
        
        theme_store.dispatch(MergeOverideComponentsAction(payload=theme))
        
        @theme_store.autorun(lambda state: state.theme)
        def _theme(_theme):
            themeSignal.changed.emit()
            
        # @theme_store.autorun(lambda state: state.theme.components)
        # def _components(_components):
        #     setThemeChanged(_components)
            
        # @theme_store.autorun(lambda state: state.theme.palette)
        # def _palette(_palette):
        #     setThemeChanged(_palette)
        
    def initUi(self):
        if isinstance(self._children, list):
            for widget in self._children:
                self.layout().addWidget(widget)
        else:
            raise AttributeError("Children must be list")
            
