"""Compatibility import for scripts written before LLM Modeling Bridge."""

import importlib
import sys

_bridge = importlib.import_module("llm_modeling_bridge")
sys.modules[__name__] = _bridge
for _name, _module in list(sys.modules.items()):
    if _name.startswith("llm_modeling_bridge."):
        sys.modules[__name__ + _name[len("llm_modeling_bridge"):]] = _module
