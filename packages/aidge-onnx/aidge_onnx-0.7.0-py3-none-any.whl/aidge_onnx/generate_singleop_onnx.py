import onnx
from onnx import helper, TensorProto, numpy_helper, shape_inference
import numpy as np

def remove_initializers_from_inputs(model: onnx.ModelProto) -> None:
    """Remove graph inputs that are also initializers."""
    initializer_names = {init.name for init in model.graph.initializer}
    # Create a new list excluding any input whose name is in initializer_names.
    new_inputs = [inp for inp in model.graph.input if inp.name not in initializer_names]
    # Clear the existing inputs and extend with the new list.
    del model.graph.input[:]
    model.graph.input.extend(new_inputs)

def create_onnx_model(operator_type: str, opset_version: int, input_properties: list[dict], intializer_rank: int = 1, **kwargs):
    """
    Create an ONNX model with a single operator using ONNX shape inference

    Args:
        operator_type (str): Type of operator (e.g., 'Conv')
        opset_version (int): opset version
        input_properties (list): List of dict (name, shapes, values) for each input tensor. Data format is NCHW. (e.g ['name'='input', 'dims'=[1,2,3,4], 'values'=None])
        intializer_rank: value above which inputs should be linked to initializers
        **kwargs: Operator-specific attributes (e.g conv_params = {'kernel_shape': (3, 3), 'strides': (2, 2),'pads': (0, 0, 0, 0)})

    Returns:
        onnx.ModelProto: Generated ONNX model
    """
    # Create input tensors info
    inputs = []
    initializers = []
    input_names = [val["name"] for val in input_properties]

    for i, property in enumerate(input_properties):
        tensor_type = TensorProto.FLOAT
        if property["values"] is not None:
            if property["values"].dtype == np.bool_:
                tensor_type = TensorProto.BOOL
            elif np.issubdtype( property["values"].dtype, np.integer):
                tensor_type = TensorProto.INT64
            elif np.issubdtype(property["values"].dtype, np.floating):
                assert(property["values"].dtype == np.float32)
                tensor_type = TensorProto.FLOAT
            else:
                raise TypeError(f"Unsupported data type in 'values'. Cannot create an initializer for the onnx.")
        if i < intializer_rank:  # First input is always the actual input
            inputs.append(helper.make_tensor_value_info(property['name'], tensor_type, property['dims']))
        else:  # Other inputs are typically weights/parameters
            if property['dims'] is None and property["values"] is None:
                input_names[i] = ''
                continue
            # data should have already been provided to the function
            tensor_data = np.array(np.random.randn(*property['dims'])).astype(np.float32) if property["values"] is None else property["values"]
            initializers.append(numpy_helper.from_array(tensor_data, name=property['name']))
            tensor_type = TensorProto.FLOAT
            if tensor_data.dtype == np.bool_:
                tensor_type = TensorProto.BOOL
            elif np.issubdtype(tensor_data.dtype, np.integer):
                tensor_type = TensorProto.INT64
            elif np.issubdtype(tensor_data.dtype, np.floating):
                tensor_data = tensor_data.astype(np.float32) # make sure it is float32
                tensor_type = TensorProto.FLOAT
            else:
                raise TypeError(f"Unsupported data type in 'values'. Cannot create an initializer for the onnx.")
            inputs.append(helper.make_tensor_value_info(property['name'], tensor_type, tensor_data.shape))

    # Create node
    node = helper.make_node(
        operator_type,
        inputs=input_names,
        outputs=['output'],
        **kwargs
    )

    # Create graph with empty output shape - will be inferred
    graph = helper.make_graph(
        [node],
        'single-operator-model',
        inputs,
        [helper.make_tensor_value_info('output', TensorProto.FLOAT, None)],
        initializers
    )

    model = helper.make_model(graph)
    model.opset_import[0].version = opset_version
    model.ir_version = 10
    # Remove constant weights from the graph inputs.
    remove_initializers_from_inputs(model)
    # Use ONNX shape inference to propagate shapes
    model = shape_inference.infer_shapes(model)

    # Validate the model
    onnx.checker.check_model(model)

    return model

# Example usage
# if __name__ == '__main__':
#     TYPE = 'Concat'

#     # Define shapes for three input tensors with same spatial dimensions but different channels
#     input_properties = [
#         {'name': 'input_0', 'dims': [1, 16, 32, 32]},  # 16 channels
#         {'name': 'input_1', 'dims': [1, 32, 32, 32]},  # 32 channels
#         {'name': 'input_2', 'dims': [1, 16, 32, 32]}   # 16 channels
#     ]

#     # Concatenate along channel axis (axis=1 in NCHW format)
#     attributes = {
#         'axis': 1  # Concatenate along channel dimension
#     }

#     model = create_onnx_model(TYPE, 12, input_properties, 3, **attributes)

#     single_operator_model_name: str = TYPE + '_model.onnx'
#     onnx.save(model, single_operator_model_name)
#     print("Model created successfully!")
#     print("Output shape:", [dim.dim_value for dim in model.graph.output[0].type.tensor_type.shape.dim])