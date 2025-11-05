"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import time
from typing import TYPE_CHECKING

import numpy as np

import aidge_core

if TYPE_CHECKING:
    from aidge_benchmark import NamedTensor


def _prepare_model_scheduler_inputs(
    model: aidge_core.GraphView, inputs: list["NamedTensor"]
) -> tuple[aidge_core.GraphView, aidge_core.SequentialScheduler]:
    # update model and inputs backend
    model_prepared = model.clone()
    model_prepared.set_backend("cpu")
    ordered_inputs = [aidge_core.Tensor(i.array) if i.array is not None else None for i in inputs]
    for ordered_input in ordered_inputs:
        if ordered_input is not None:
            ordered_input.set_backend("cpu")

    scheduler = aidge_core.SequentialScheduler(model_prepared)
    scheduler.generate_scheduling()

    return model_prepared, scheduler, ordered_inputs


def measure_inference_time(
    model: aidge_core.GraphView,
    inputs: list["NamedTensor"],
    nb_warmup: int = 10,
    nb_iterations: int = 50,
) -> list[float]:
    _, scheduler, ordered_inputs = _prepare_model_scheduler_inputs(model, inputs)

    timings = []
    # Warm-up runs.
    for i in range(nb_warmup + nb_iterations):
        if i < nb_warmup:
            scheduler.forward(forward_dims=False, data=ordered_inputs)
        else:
            start = time.process_time()
            scheduler.forward(forward_dims=False, data=ordered_inputs)
            end = time.process_time()
            timings.append((end - start))
    return timings


def compute_output(
    model: aidge_core.GraphView, inputs: list["NamedTensor"]
) -> list[np.ndarray]:
    model_prepared, scheduler, ordered_inputs = _prepare_model_scheduler_inputs(model, inputs)

    scheduler.forward(forward_dims=False, data=ordered_inputs)

    return [
        np.array(t[0].get_operator().get_output(t[1]))
        for t in model_prepared.get_ordered_outputs()
    ]
