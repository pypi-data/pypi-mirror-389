from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from ...theme_reducer import ThemeState

from ..properties_name import *
from .....system.color_manipulator import alpha

def py_input(_theme):
    theme: ThemeState = _theme

    _color = {
        'focused': theme.palette.text.primary,
        'active': theme.palette.text.secondary,
        'placeholder': theme.palette.text.disabled,
    }

    return {
        'PyInput': {
            'styles': {
                'root': {
                    margin: "0px",
                    marginTop: "6px",
                    backgroundColor: "transparent",
                    border: f"1px solid transparent",
                    borderRadius: f'{theme.shape.borderRadius}px',
                    fontSize: "11px",
                },
                "title": {
                    subcontrolOrigin: "margin",
                    left:theme.spacing(1),
                    border: "1px solid transparent",
                    borderRadius: theme.spacing(1),
                    height: int(theme.spacing(1).replace("px", "")),
                    color: _color['active'],
                    "slots": {
                        'focused': {
                            color: _color['focused']
                        },
                        'error': {
                            color: theme.palette.error.main
                        },
                        'disabled': {
                            color: theme.palette.text.disabled
                        },
                        'filled': {
                            backgroundColor: "transparent",
                        },
                        'standardVariant': {
                            marginLeft: "0px",
                        },
                    },
                },
                "inputField": {
                    lineHeight: theme.typography.body2.lineHeight,
                    fontSize: theme.typography.body2.fontSize,
                    fontWeight: 600,
                    paddingRight: "54px",
                    color: theme.palette.text.primary,
                    "props": {
                        "multiline": {
                            "small": {
                                paddingTop: "12px",
                            },
                            "medium": {
                                paddingTop: "16px",
                            },
                        },
                        "multiple": {
                            paddingTop: "0px",
                            paddingLeft: "0px",
                        },
                    }
                }
            },
        },
        'PyInputSize': {
            'styles': {
                'small': {
                    fontSize: 13,
                    # paddingLeft: 8,
                    # paddingRight: 8,
                    'no-multiple': {
                        height: "32px", #32 # mui 4
                    },
                    'filledVariant': {
                        height: "22px", #32 # mui 4
                    },
                    'dateTimeType': {
                        paddingLeft: f"{theme.spacing(3)}"
                    }
                },
                'medium': {
                    fontSize: 13,
                    # paddingLeft: 12,
                    # paddingRight: 12,
                    'no-multiple': {
                        height: "38px", # mui 4
                    },
                    'filledVariant': {
                        height: "38px", # mui 4
                    },
                    'dateTimeType': {
                        paddingLeft: f"{theme.spacing(4)}"
                    }
                },

            }
        }
    }