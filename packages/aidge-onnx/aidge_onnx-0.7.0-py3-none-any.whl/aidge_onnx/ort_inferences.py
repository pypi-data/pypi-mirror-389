import numpy as np
import onnx
from typing import Dict
from aidge_onnx.utils import onnx_to_aidge_name

from aidge_core.benchmark.output_wise_comparison import (
    OutputTensorMap,
    RunResult
)

ORT_AVAILABLE = True
try:
    import onnxruntime as ort
except ImportError as e:
    ORT_AVAILABLE = False

def generate_random_inputs_from_onnx(model: onnx.ModelProto) -> Dict[str, np.ndarray]:
    inputs = {}
    initializer_names = [x.name for x in model.graph.initializer]
    for inp in model.graph.input:
        # Skip initializers
        if inp.name in initializer_names: continue
        shape = []
        for dim in inp.type.tensor_type.shape.dim:
            if dim.dim_value > 0:
                shape.append(dim.dim_value)
            else:
                shape.append(1)  # Use 1 as a fallback for unknown dimensions
        dtype = inp.type.tensor_type.elem_type
        np_dtype = onnx.mapping.TENSOR_TYPE_TO_NP_TYPE.get(dtype, np.float32)
        rand_input = np.random.rand(*shape).astype(np_dtype)
        inputs[inp.name] = rand_input
    return inputs

def run_ort_outputwise_benchmark(model: onnx.ModelProto, inputs: Dict[str, np.ndarray]) -> OutputTensorMap:
    if not ORT_AVAILABLE: raise ImportError("ONNX Runtime is not available please use `pip install onnxruntime`.")
    # Create a set of Constant node to ignore them
    constant_nodes_name = set(output for node in model.graph.node if node.op_type == "Constant" for output in node.output)
    # Set every output Tensor as a graph output (except constant ...)
    shape_info = onnx.shape_inference.infer_shapes(model)
    for node in shape_info.graph.value_info:
        if node.name not in constant_nodes_name:
            model.graph.output.append(node)
    session = ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])

    # Gather internal and final outputs
    intermediate_names = [v.name for v in model.graph.value_info]
    output_names = [o.name for o in model.graph.output]
    all_outputs = list(set(intermediate_names + output_names))
    # Run inference
    ort_outs = session.run(all_outputs, inputs)
    # Generate result dictionary

    ordered_output_names = []
    for node in model.graph.node:
        if node.op_type != "Constant":
            ordered_output_names.extend(node.output)

    return RunResult(
        edge_tensor_map={onnx_to_aidge_name(name): val for name, val in zip(all_outputs, ort_outs)},
        topological_order=[onnx_to_aidge_name(out_name) for n in model.graph.node for out_name in n.output if n.op_type != "Constant"]
    )
