import argparse
import onnx
import aidge_core
import aidge_backend_cpu
import time
from pathlib import Path
from typing import List, Dict
from collections import Counter
from rich.table import Table
from rich.console import Console
import numpy as np

ORT_AVAILABLE = True
try:
    import onnxruntime as ort
except ImportError as e:
    ORT_AVAILABLE = False
from .recipes import RECIPES
from .onnx_import import convert_onnx_to_aidge, has_native_coverage, native_coverage_report
from .onnx_export import convert_aidge_to_onnx
from .onnx_test import check_onnx_validity
from .utils import get_inputs
from .ort_inferences import generate_random_inputs_from_onnx

def _parse_shapes(shapes_arg: str) -> Dict[str, List[int]]:
    """Helper function to parse argument shape

    :param shapes_arg: Argument
    :type shapes_arg: str
    :return: _description_
    :rtype: Dict[str, List[List[int]]]
    """
    shapes = {}
    if shapes_arg is not None:
        for x in shapes_arg:
            if ':' not in x:
                shapes[None] = list(map(int, x.split(',')))
            else:
                pieces = x.split(':')
                # for the input name like input:0
                name, shape = ':'.join(
                    pieces[:-1]), list(map(int, pieces[-1].split(',')))
                if name in shapes:
                    shapes[name].append(shape)
                else:
                    shapes.update({name: [shape]})
    return shapes

def _forward_dims(graph_view: aidge_core.GraphView, input_shape: List[int])->bool:
    if not has_native_coverage(graph_view):
        native_coverage_report(graph_view)
        raise RuntimeError("Native coverage is not complete. Please check the coverage report above.")
    # TODO:
    # - Add support for dims with multi input
    if len(input_shape) !=1:
        raise ValueError("More than one shape given")
    graph_view.set_backend("cpu")
    graph_view.forward_dtype()

    if not graph_view.forward_dims(list(input_shape.values())[0], allow_data_dependency = False):
        aidge_core.Log.info("Could not forward dims.")

def _str_size(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def _show_cleaning_results(onnx_1, onnx_2):

    gv_1_cpt = Counter([n.op_type for n in onnx_1.graph.node])
    gv_2_cpt = Counter([n.op_type for n in onnx_2.graph.node])

    size_1 = onnx_1.ByteSize()
    size_2 = onnx_2.ByteSize()

    table = Table(show_header=True, header_style="bold")
    table.add_column("", style="bold")
    table.add_column("Original Model", justify="right")
    table.add_column("Simplified Model", justify="right")

    all_types = set(gv_1_cpt.keys()).union(gv_2_cpt.keys())
    for node_type in sorted(all_types):
        nb_nodes_1 = gv_1_cpt.get(node_type, 0)
        nb_nodes_2 = gv_2_cpt.get(node_type, 0)

        if nb_nodes_2 < nb_nodes_1:
            style = "green"
        elif nb_nodes_2 > nb_nodes_1:
            style = "red"
        else:
            style = "yellow"

        table.add_row(node_type, f"{nb_nodes_1}", f"[{style}]{nb_nodes_2}[/{style}]")

    if size_2 < size_1:
        style = "green"
    elif size_2 > size_1:
        style = "red"
    else:
        style = "yellow"

    table.add_row("Model Size",
                  _str_size(size_1),
                  f"[{style}]{_str_size(size_2)}[/{style}]")

    console = Console()
    console.print(table)

def is_shape_compatible(ref_shape, other_shape):
    """Check if two shape are compatible.
    That is if every dimensions are equal.
    This function skip dynamic shape.
    """
    if len(ref_shape) != len(other_shape):
        return False
    for r_dim, o_dim in zip(ref_shape, other_shape):
        if isinstance(r_dim, str) or r_dim is None:
            continue
        if isinstance(o_dim, str) or o_dim is None:
            continue
        if r_dim != o_dim:
            return False
    return True

def compare_inferences(base_model, cleaned_model, atol=1e-5, rtol=1e-3) -> bool:
    if not ORT_AVAILABLE: raise ImportError("Failed to import onnxruntime, make sure it is installed.")
    sess_base = ort.InferenceSession(base_model.SerializeToString())
    sess_clean = ort.InferenceSession(cleaned_model.SerializeToString())

    base_inputs_info  = {i.name: i for i in sess_base.get_inputs()}
    clean_inputs_info  = {i.name: i for i in sess_clean.get_inputs()}

    # Link base name with cleaned name
    input_map = {}
    used_inputs = set()
    for ref_name, ref in base_inputs_info.items():
        if ref_name in clean_inputs_info:
            # Try to match by name
            input_map[ref_name] = ref_name
            used_inputs.add(ref_name)
        else:
            # Try to match by shape
            for other_name, other in clean_inputs_info.items():
                if other_name in used_inputs:
                    continue
                if is_shape_compatible(ref.shape, other.shape):
                    input_map[ref_name] = other_name
                    used_inputs.add(other_name)
                    break
            else:
                raise ValueError(
                    f"Could not match input/output: '{ref_name}' with shape {ref.shape}"
                )

    # Generate random input based on the base model's inputs
    base_inputs = generate_random_inputs_from_onnx(base_model)
    # Set the input to the corresponding ones of the cleaned model
    clean_inputs = {input_map[k]: v for k, v in base_inputs.items()}

    base_outputs = sess_base.run(None, base_inputs)
    clean_outputs = sess_clean.run(None, clean_inputs)

    all_passed = True
    for base_out, clean_out in zip(base_outputs, clean_outputs):
        if base_out.shape != clean_out.shape:
            aidge_core.Log.notice(f"Shape mismatch: {base_out.shape} vs {clean_out.shape}")
            all_passed = False
        if not np.allclose(base_out, clean_out, atol=atol, rtol=rtol):
            aidge_core.Log.notice(f"Values differ (max abs diff: {np.max(np.abs(base_out - clean_out))})")
            all_passed = False,
    return all_passed

def show_available_recipes():
    console = Console()
    table = Table(title="Available Graph Transformation Recipes")

    table.add_column("Recipe", style="bold", no_wrap=True)
    table.add_column("Supported Opsets", style="bold yellow", justify="center")
    table.add_column("Training-Safe", justify="center")
    table.add_column("Accuracy-Safe", justify="center")
    table.add_column("Brief", style="green")

    max_opset = onnx.defs.onnx_opset_version()
    for recipe in RECIPES:
        supported = [str(opset) for opset in range(max_opset + 1) if recipe.is_compatible_opset(opset)]

        training_safe = "[green]✓[/]" if recipe.training_safe else "[red]✗[/]"
        accuracy_safe = "[green]✓[/]" if recipe.accuracy_safe else "[red]✗[/]"

        # Collapse into ranges for readability, e.g. "0-22"
        if len(supported) == max_opset + 1:
            supported_str = "All"
        else:
            supported_str = _compress_opset_list(supported)

        table.add_row(
            recipe.__name__,
            supported_str,
            training_safe,
            accuracy_safe,
            getattr(recipe, "brief", "")
        )

    console.print(table)

def _compress_opset_list(opsets: list[str]) -> str:
    """Compress a list of numeric strings into ranges, e.g. ['1','2','3','5'] -> '1-3, 5'."""
    opsets = list(map(int, opsets))
    opsets.sort()
    ranges = []
    start = prev = opsets[0]
    for num in opsets[1:]:
        if num == prev + 1:
            prev = num
        else:
            ranges.append((start, prev))
            start = prev = num
    ranges.append((start, prev))
    return ', '.join(f"{s}" if s == e else f"{s}-{e}" for s, e in ranges)

def simplify_graph(
        graph_view: aidge_core.GraphView,
        input_shape: Dict[str, List[int]],
        skip:List[str]=None,
        training_safe:bool=True,
        allow_nonexact:bool=False
    )->None:
    if skip is None: skip = []
    verbose_activated = int(aidge_core.Log.get_console_level()) <= int(aidge_core.Level.Notice)

    aidge_core.Log.notice("Simplifying ...")
    for recipe in RECIPES:
        if recipe.__name__ in skip:
            aidge_core.Log.notice(f"Skipping recipe: {recipe.__name__}")
            skip.remove(recipe.__name__)
            continue
        if (not recipe.training_safe) and (training_safe):
            continue
        if (not recipe.accuracy_safe) and (not allow_nonexact):
            continue
        aidge_core.Log.notice(f"Applying recipe: {recipe.__name__}")
        if verbose_activated: start = time.perf_counter()
        recipe.apply(graph_view)
        if verbose_activated: aidge_core.Log.notice(f"{recipe.__name__} applied in {time.perf_counter() - start:.6f} seconds")
        # Always forwardDims back as simplification may have remove tensor
        graph_view.forward_dims(list(input_shape.values())[0], allow_data_dependency = True)
    if skip:
        skipped_recipes_str = '\n\t- '.join(skip)
        aidge_core.Log.warn(f"The following recipes were not found:\n\t- {skipped_recipes_str}")

def infer_input_shape(onnx_model: onnx.ModelProto)->Dict[str, List[int]]:
    return {input_dict['name']: [input_dict['dims']] for input_dict in get_inputs(onnx_model)}

def clean_onnx(
        onnx_to_clean: onnx.ModelProto,
        input_shape:Dict[str, List[int]],
        name:str,
        ir_version:int=None,
        opset_version:int=None,
        compare:bool=True,
        skip:List[str]=None,
        training_safe:bool=True,
        allow_nonexact:bool=False
        ) -> onnx.ModelProto:
    """
    Simplifies an ONNX model and returns the processed graph.
    """
    if input_shape == {}:
        input_shape = infer_input_shape(onnx_to_clean)

    aidge_core.Log.debug(f"Using the following input shape:\n")
    for key, value in input_shape.items():
        aidge_core.Log.debug(f"\t-{key}: {value}")

    graph_view = convert_onnx_to_aidge(onnx_to_clean)
    # Transformation to have a valid Aidge graph
    aidge_core.remove_flatten(graph_view)
    _forward_dims(graph_view, input_shape)

    simplify_graph(
        graph_view,
        input_shape,
        skip=skip,
        training_safe=training_safe,
        allow_nonexact=allow_nonexact)

    # Forward dims again in case one of the input node got removed
    _forward_dims(graph_view, input_shape)


    onnx_cleaned = convert_aidge_to_onnx(
        graph_view,
        name,
        opset=opset_version,
        ir_version=ir_version,
    )
    if not check_onnx_validity(onnx_cleaned):
        aidge_core.Log.warn("The generated ONNX is not valid.")

    _show_cleaning_results(onnx_to_clean, onnx_cleaned)

    if compare:
        equivalent = compare_inferences(onnx_to_clean, onnx_cleaned)
        if not equivalent:
            print("Cleaned ONNX diverge from based ONNX.")
        else:
            print("Cleaned model is equivalent in inference to the base model!")
    return onnx_cleaned

def clean_file(
        model_path: str,
        output_path: str,
        input_shape: Dict[str, List[int]],
        ir_version=None,
        opset_version=None,
        compare=True,
        skip:List[str]=None,
        training_safe:bool=True,
        allow_nonexact:bool=False
    ) -> None:
    onnx_to_clean = onnx.load(model_path)

    output_path = Path(output_path)
    new_onnx_name = output_path.stem
    onnx_cleaned = clean_onnx(
        onnx_to_clean,
        input_shape,
        new_onnx_name,
        ir_version=ir_version,
        opset_version=opset_version,
        compare=compare,
        skip=skip,
        training_safe=training_safe,
        allow_nonexact=allow_nonexact
    )
    aidge_core.Log.notice(f"Saving {output_path}")
    onnx.save(onnx_cleaned, output_path)

def onnx_cleaner_cli():
    """Handle argument parsing and call :py:func:`aidge_onnx.onnx_sim`.
    This function is exposed as a project script by pyproject.toml.
    """
    parser = argparse.ArgumentParser()
    # === Positional args ===
    parser.add_argument('input_model', nargs="?", help="Path to the input ONNX model.")
    parser.add_argument('output_model', nargs="?", help="Path to save the simplified ONNX model.")

    # === Helper group ===
    helper_group = parser.add_argument_group("helper / debugging")
    helper_group.add_argument(
        "--show_recipes",
        action="store_true",
        help="Show available recipes."
    )
    helper_group.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help=(
            "Set the verbosity level of console output. "
            "Use -v, -vv, -vvv to increase verbosity."
        )
    )

    # === Model I/O and format group ===
    io_group = parser.add_argument_group("format options")
    io_group.add_argument(
        "--input-shape",
        type=str,
        nargs="+",
        help=(
            "Overwrite the input shape.\n"
            "Format: \"input_name:dim0,dim1,...\" or just \"dim0,dim1,...\" "
            "if only one input.\n"
            "Example: \"data:1,3,224,224\" or \"1,3,224,224\"."
        ),
    )
    io_group.add_argument(
        "--ir-version",
        type=int,
        default=None,
        help="Specify ONNX IR version to save the model with. Default: let ONNX decide."
    )
    io_group.add_argument(
        "--opset-version",
        type=int,
        default=None,
        help="Specify ONNX opset version to save the model with. Default: let ONNX decide."
    )

    # === Optimization group ===
    opt_group = parser.add_argument_group("optimization options")
    opt_group.add_argument(
        "-O", "--opt-level",
        type=int,
        choices=[0, 1, 2],
        default=1,
        help=(
            "Optimization level:\n"
            "  0 = training-safe (minimal)\n"
            "  1 = accuracy-safe (exact)\n"
            "  2 = approximate perf optimizations"
        )
    )
    opt_group.add_argument(
        "--training-safe",
        action="store_true",
        help="Resulting graph remains learnable (overrides -O if needed)."
    )
    opt_group.add_argument(
        "--allow-nonexact",
        action="store_true",
        help="Permit optimizations that may change outputs (accuracy-unsafe) for performance gains (overrides -O if needed)."
    )
    opt_group.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Skip specific recipes by class name (e.g. --skip FuseGeLU FuseLayerNorm)."
    )
    opt_group.add_argument(
        "--compare",
        action="store_true",
        help="Run inference with both original and optimized model, compare results."
    )

    args = parser.parse_args()
    if args.show_recipes:
        show_available_recipes()
        exit()

    if not args.input_model or not args.output_model:
        parser.error("the following arguments are required: input_model, output_model")

    # Setting Aidge verbose level
    if args.verbose == 0:
        aidge_core.Log.set_console_level(aidge_core.Level.Warn)
    elif args.verbose == 1:
        aidge_core.Log.set_console_level(aidge_core.Level.Notice)
    elif args.verbose == 2:
        aidge_core.Log.set_console_level(aidge_core.Level.Info)
    elif args.verbose >= 3:
        aidge_core.Log.set_console_level(aidge_core.Level.Debug)


    if args.opt_level == 0:
        training_safe = True
        allow_nonexact = False
    elif args.opt_level == 1:
        training_safe = False
        allow_nonexact = False
    elif args.opt_level == 2:
        training_safe = False
        allow_nonexact = True
    else:
        raise ValueError(f"Unexpected opt_level {args.opt_level}.")

    if args.training_safe:
        training_safe = True
    if args.allow_nonexact:
        allow_nonexact = True

    input_shape: Dict[str, List[int]] = _parse_shapes(args.input_shape)

    clean_file(
        args.input_model,
        args.output_model,
        input_shape,
        ir_version=args.ir_version,
        opset_version=args.opset_version,
        compare=args.compare,
        skip=args.skip,
        training_safe=training_safe,
        allow_nonexact=allow_nonexact
    )


if __name__ == "__main__":
    onnx_cleaner_cli()