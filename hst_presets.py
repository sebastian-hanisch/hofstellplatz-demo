"""Regler-Spezifikation, Permalink, Presets und Seed-Knopf (Standardmuster aus dem OR-Demo-Portfolio,
siehe blz_presets.py/gate_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import hst_constants as C


def _depth(raw):
    value = int(round(float(raw)))
    if value not in C.DEPTH_LEVELS:
        raise ValueError(raw)
    return value


def _int_text(value):
    return str(int(value))


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None
    step: Optional[int] = None
    encoder: Callable = _int_text


SETTING_SPECS = {
    "rows_slider": SettingSpec("r", int, C.ROWS_DEFAULT, *C.ROWS_RANGE, 1),
    "depth_radio": SettingSpec("h", _depth, C.DEPTH_DEFAULT, min(C.DEPTH_LEVELS), max(C.DEPTH_LEVELS), 1),
    "n_items_slider": SettingSpec("n", int, C.N_ITEMS_DEFAULT, *C.N_ITEMS_RANGE, 1),
    "window_slider": SettingSpec("w", int, C.WINDOW_DEFAULT, *C.WINDOW_RANGE, 1),
    "dwell_slider": SettingSpec("d", int, C.DWELL_DEFAULT, *C.DWELL_RANGE, 1),
    "sigma_slider": SettingSpec("sg", int, C.SIGMA_DEFAULT, *C.SIGMA_RANGE, C.SIGMA_STEP),
    "seed_input": SettingSpec("seed", int, C.SEED_DEFAULT, *C.SEED_RANGE, 1),
}

PRESET_STATE_KEYS = {"rows": "rows_slider", "depth": "depth_radio", "n_items": "n_items_slider", "window": "window_slider", "dwell": "dwell_slider", "sigma": "sigma_slider", "seed": "seed_input"}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def parse_setting(spec, raw):
    try:
        value = spec.caster(raw)
    except (ValueError, TypeError):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    if spec.step and spec.step > 1 and spec.lo is not None:
        value = spec.lo + round((value - spec.lo) / spec.step) * spec.step
        value = min(spec.hi, value)
    return value


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            value = parse_setting(spec, qp[spec.url_param])
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = SETTING_SPECS[state_key].encoder(value)
    except Exception:
        pass


def apply_preset(name):
    for field, state_key in PRESET_STATE_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][field]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(*C.SEED_RANGE)
