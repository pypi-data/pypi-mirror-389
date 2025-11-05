import argparse
import onnx
import aidge_core
from pathlib import Path
from aidge_onnx import (
    convert_onnx_to_aidge,
    run_ort_outputwise_benchmark,
    generate_random_inputs_from_onnx
)
from aidge_onnx.utils import set_every_out_as_graph_out
from aidge_core.benchmark.output_wise_comparison import (
    run_aidge_outputwise_benchmark,
    compare_outputs,
    render_results_table,
    save_comparison_differences
)

## Utils function
def compare_ort_aidge():
    parser = argparse.ArgumentParser(description="Compare ONNXRuntime with Aidge")
    parser.add_argument("model_path", type=str, help="Path to the ONNX model")
    parser.add_argument("--log-dir", type=str, default=None, help="Directory to save result logs (optional)")
    parser.add_argument("--atol", type=float, default=1e-4, help="Set the absolute precision to compare each value of the intermediate outputs")
    parser.add_argument("--rtol", type=float, default=1e-3, help="Set the relative precision to compare each value of the intermediate outputs")

    args = parser.parse_args()

    model_path = args.model_path
    aidge_core.Log.set_console_level(aidge_core.Level.Fatal)

    # Load model
    model = onnx.load(model_path)
    set_every_out_as_graph_out(model)
    # Create Aidge model
    graph_view = convert_onnx_to_aidge(model)

    # Prepare inputs
    input_data = generate_random_inputs_from_onnx(model)


    # Run inferences
    onnx_outputs = run_ort_outputwise_benchmark(model, input_data)
    aidge_outputs = run_aidge_outputwise_benchmark(graph_view, input_data)

    # Compare and render
    results = compare_outputs(onnx_outputs, aidge_outputs, atol=args.atol, rtol=args.rtol)
    render_results_table(results, "ONNX Runtime", "Aidge", Path(model_path).stem)

    if args.log_dir:
        save_comparison_differences(results, output_dir=args.log_dir)

if __name__ == "__main__":
    compare_ort_aidge()
