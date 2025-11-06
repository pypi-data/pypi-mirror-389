"""This submodule contains function to adapt the graph to the ONNX standard QDQ and QOP.
Once the graph has been adapted you can simply call the ONNX export function from the aidge_onnx module.
"""

from .qdq import set_to_qdq
from .qop import set_to_qop