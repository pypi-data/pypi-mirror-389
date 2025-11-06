import aidge_core
import aidge_quantization

OPS_WITH_BIAS = [
    "FC",
    "Conv1D", "Conv2D", "Conv3D",
    "ConvDepthWise1D", "ConvDepthWise2D", "ConvDepthWise3D",
    "PaddedConv1D", "PaddedConv2D", "PaddedConv3D",
    "PaddedConvDepthWise1D", "PaddedConvDepthWise2D", "PaddedConvDepthWise3D"
]

TRANSPARENT_OPS = [
    "ReLU"
]

def Dequantizer(scale: float, base_name: str, backend:str) -> aidge_core.Node:
    """
    Factory function to create a dequantizer node.

    Note: This may need to be placed in PTQMetaOps.cpp.
    """
    mul_op = aidge_core.Mul(name = base_name + "_dq_scaling")
    scaling_prod = aidge_core.Producer(aidge_core.Tensor(scale, backend=backend), base_name+"_dq_scale_factor")

    x = aidge_core.Connector()
    s = aidge_core.Connector()

    cast_op  = aidge_core.Cast(aidge_core.dtype.float32, name = base_name+"_dq_cast")
    micro_graph = aidge_core.generate_graph([mul_op(cast_op(x), s)])
    scaling_prod.add_child(mul_op, 0, 1)
    micro_graph.add(scaling_prod)
    mul_op.get_operator().set_datatype(aidge_core.dtype.float32)

    micro_graph.set_backend(backend)
    dq_node = aidge_core.meta_operator(
        "Dequantizer",
        micro_graph,
        name = base_name
    )
    dq_node.get_operator().set_datatype(aidge_core.dtype.float32)

    return dq_node

def fold_bias(graph_view):

    def _is_int32_quant(node):
        is_int32 = False
        for n in node.get_operator().get_micro_graph().get_nodes():
            if n.type() == "Cast" and n.get_operator().attr.target_type == aidge_core.dtype.int32:
                is_int32 = True
                break
        return is_int32

    spgm = aidge_core.SinglePassGraphMatching(graph_view)
    spgm.add_node_lambda("int32", _is_int32_quant)
    matches = spgm.match("Producer#0->Quantizer#1[int32];")
    for match in matches:
        matched_graph = match.graph.clone()
        for n in matched_graph.get_nodes():
            if n.type() == "Producer":
                n.get_operator().attr.constant = True
        aidge_core.constant_folding(matched_graph)
        if (not aidge_core.GraphView.replace(match.graph, matched_graph)):
            raise RuntimeError("Failed to constant fold bias.")

def set_to_qdq(graph_view):
    """
    Transform a freshly quantized model to QDQ format.

    This function is only guaranteed to work on quantized graph that haven't been modified!
    """
    ### Create a topologically ordered list of nodes
    ordered_nodes = graph_view.get_ordered_nodes()
    for node in ordered_nodes:
        if node.type() in ["Producer", "Quantizer", "Dequantizer"]:
            continue

        if node.type() in OPS_WITH_BIAS:
            scales = []
            # 1. Add Dequantize layer to inputs
            parents = node.get_parents()
            for in_id, parent_node in enumerate(parents):
                if parent_node is None:
                    if in_id == 3:
                        scales.append(None)
                        continue
                    else:
                        raise RuntimeError(f"Node {node.name()} was expected to have a Quantizer at input {in_id} but no parent was found.")

                if parent_node.type() != "Quantizer":
                    raise RuntimeError(f"Node {node.name()} was expected to have a Quantizer as a parent, got {parent_node.name()}[{parent_node.type()}] instead.")

                scale = aidge_quantization.get_scaling_factor(parent_node)
                scales.append(scale)

                # Insert Dequantizer Node
                graph_view.insert_parent(
                    node,
                    Dequantizer(
                        1/scale,
                        f"{node.name()}_{in_id}_dq",
                        node.get_operator().backend()
                    ),
                    in_id,
                    0,
                    0
                )
            children = node.get_children()
            if len(children) != 1:
                raise RuntimeError(f"{node.name()}[{node.type()}] should have 1 output, found {len(children)} instead")

            # 2. Compensate outputs + bias (if any)
            # 2.1 Compensate output scaling
            child_node = list(children)[0]
            if child_node.type() != "Quantizer":
                raise RuntimeError(f"Node {node.name()} was expected to have a Quantizer as a child, got {child_node.name()}[{child_node.type()}] instead.")

            output_scale = aidge_quantization.get_scaling_factor(child_node)
            # Multiply by input and weight scale
            aidge_quantization.set_scaling_factor(
                child_node,
                output_scale * scales[0] * scales[1]
            )

            # 2.2 Compensate bias scaling
            if scales[2] is None:
                # No scaling, skip
                continue
            # Update bias scale.
            aidge_quantization.set_scaling_factor(
                parents[2],
                (scales[2]**2) / (scales[0] * scales[1])
            )

        elif node.type() in TRANSPARENT_OPS:
            parents = node.get_parents()
            if len(parents) != 1:
                raise RuntimeError(f"{node.name()}[{node.type()}] should have 1 input, found {len(parents)} instead")

            parent_node = parents[0]

            if parent_node.type() != "Quantizer":
                raise RuntimeError(f"Node {node.name()} was expected to have a Quantizer as a parent, got {parent_node.name()}[{parent_node.type()}] instead.")

            scale = aidge_quantization.get_scaling_factor(parent_node)

            # 1. Insert Dequantizer Node
            graph_view.insert_parent(
                node,
                Dequantizer(
                    1/scale,
                    f"{node.name()}_dq",
                    node.get_operator().backend()
                ),
                0, # child in idx
                0, # New parent in idx
                0  # New parent out idx
            )
            # 2. Insert compensation Quantizer Node
            if node.get_nb_outputs() != 1:
                raise RuntimeError(f"{node.name()}[{node.type()}] should have 1 output, found {node.nb_outputs()} instead")

            quantizer_node = aidge_core.Quantizer(
                scaling_factor=scale,
                name=f"{node.name()}_quantizer",
                round=True,
                clip_min=-128,
                clip_max=127,
                # to_type=aidge_core.dtype.int8,
            )

            quantizer_node.get_operator().set_backend(node.get_operator().backend())
            quantizer_node.get_operator().set_datatype(aidge_core.dtype.float32)
            aidge_quantization.cast_quantizer_ios(quantizer_node, aidge_core.dtype.int8)

            graph_view.add(quantizer_node)
            for output_node, out_in_id in node.output(0):
                graph_view.insert_parent(
                    output_node,
                    quantizer_node,
                    out_in_id,
                    0,
                    0
                )
            node.add_child(quantizer_node, 0, 0)
        else:
            raise RuntimeError(f'Cannot treat operator of type {node.type()}')
    fold_bias(graph_view)
    graph_view.forward_dtype()