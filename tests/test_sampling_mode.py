"""CPU-only contract fixtures; do not establish real-worker activation.

Load the leaf module by file path, avoiding vllm_ascend package imports.
Request-state tests extract the real builder and sampling guard with AST,
without importing the runner or replacing their logic with test implementations.
"""

import ast
from dataclasses import FrozenInstanceError, replace
import gc
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
import weakref


SOURCE_ROOT = Path(os.environ["STATEAXIS_COMPACT_DRAFT_SOURCE"])
MODULE_PATH = SOURCE_ROOT / "vllm_ascend/sample/sampling_mode.py"
spec = importlib.util.spec_from_file_location("_compact_sampling_mode_fixture", MODULE_PATH)
mode = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mode
spec.loader.exec_module(mode)


def params(**changes):
    values = dict(
        sampling_type=NS(name="GREEDY"), logprobs=None, prompt_logprobs=None,
        logprob_token_ids=None, structured_outputs=None, thinking_token_budget=None,
        min_tokens=0, logit_bias={}, allowed_token_ids=None, bad_words_token_ids=[],
        presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0,
    )
    values.update(changes)
    return NS(**values)


class RequestState:
    """Weak-referenceable stand-in; no real worker activation is implied."""

    def __init__(self, **values):
        self.__dict__.update(values)

    def __eq__(self, other):
        # Distinct but equal-valued states must still fail an identity guard.
        return isinstance(other, RequestState) and self.__dict__ == other.__dict__


def request(*, sampling_params=None, **changes):
    values = dict(
        sampling_params=params() if sampling_params is None else sampling_params,
        lora_request=None, mm_features=[], prompt_embeds=None, num_prompt_tokens=8,
        # Deliberately differs from scheduler facts; selector must ignore it.
        num_computed_tokens=-100,
    )
    values.update(changes)
    return RequestState(**values)


def scheduler(*, scheduled=None, cached=None, new=(), **changes):
    scheduled = {"r": 1} if scheduled is None else scheduled
    cached = [("r", 8)] if cached is None else cached
    values = dict(
        total_num_scheduled_tokens=sum(scheduled.values()),
        has_structured_output_requests=False, pending_structured_output_tokens=False,
        scheduled_spec_decode_tokens={}, scheduled_encoder_inputs={},
        num_scheduled_tokens=scheduled,
        scheduled_cached_reqs=NS(
            req_ids=[key for key, _ in cached],
            num_computed_tokens=[computed for _, computed in cached],
        ),
        scheduled_new_reqs=[NS(req_id=key, num_computed_tokens=computed) for key, computed in new],
    )
    values.update(changes)
    return NS(**values)


class EligibilityTests(unittest.TestCase):
    def eligible(self, req=None, output=None):
        return mode.plain_decode_request_ids(
            scheduler() if output is None else output,
            {"r": request() if req is None else req},
        )

    def test_plain_greedy_decode(self):
        self.assertEqual(self.eligible(), ("r",))

    def test_original_logprob_requests_including_zero_and_empty_token_list(self):
        # 0 still requests the sampled token's logprob; truthiness is unsafe.
        for field, value in (
            ("logprobs", 0), ("logprobs", 2),
            ("prompt_logprobs", 0), ("prompt_logprobs", 1),
            ("logprob_token_ids", []), ("logprob_token_ids", [7]),
        ):
            with self.subTest(field=field, value=value):
                self.assertIsNone(self.eligible(request(sampling_params=params(**{field: value}))))

    def test_lifetime_exclusions_not_inferred_from_current_processor_state(self):
        for field, value in (
            ("structured_outputs", NS()),
            ("thinking_token_budget", 0), ("thinking_token_budget", 16),
            ("min_tokens", 1), ("logit_bias", {7: 0.25}),
            ("allowed_token_ids", [7, 8]), ("bad_words_token_ids", [[7, 8]]),
            ("presence_penalty", 0.5), ("presence_penalty", -0.5),
            ("frequency_penalty", 0.5), ("repetition_penalty", 1.1),
        ):
            with self.subTest(field=field, value=value):
                req = request(sampling_params=params(**{field: value}))
                req.output_token_ids = list(range(100))
                self.assertIsNone(self.eligible(req))

    def test_absent_allowlist_empty_bias_badwords_and_neutral_penalties(self):
        req = request(sampling_params=params(allowed_token_ids=None, logit_bias={},
                                             bad_words_token_ids=[]))
        self.assertEqual(self.eligible(req), ("r",))

    def test_missing_sampling_params_and_nontext_or_adapter_requests(self):
        for field, value in (
            ("sampling_params", None), ("lora_request", NS()),
            ("mm_features", [NS()]), ("prompt_embeds", NS()),
        ):
            with self.subTest(field=field):
                req = request()
                setattr(req, field, value)
                self.assertIsNone(self.eligible(req))

    def test_mixed_greedy_random_falls_back_for_entire_batch(self):
        output = scheduler(scheduled={"greedy": 1, "random": 1},
                           cached=[("greedy", 8), ("random", 8)])
        requests = {
            "greedy": request(),
            "random": request(sampling_params=params(sampling_type=NS(name="RANDOM"))),
        }
        self.assertIsNone(mode.plain_decode_request_ids(output, requests))
        requests["random"].sampling_params = params()
        self.assertEqual(mode.plain_decode_request_ids(output, requests), ("greedy", "random"))

    def test_prefill_final_single_token_is_not_yet_decode(self):
        for computed, expected in ((0, None), (6, None), (7, None),
                                   (8, ("r",)), (9, ("r",))):
            with self.subTest(computed=computed):
                self.assertEqual(self.eligible(output=scheduler(cached=[("r", computed)])), expected)

    def test_multitoken_prefill_or_decode_batch_is_excluded(self):
        for computed in (0, 7, 8, 20):
            with self.subTest(computed=computed):
                output = scheduler(scheduled={"r": 2}, cached=[("r", computed)])
                self.assertIsNone(self.eligible(output=output))

    def test_cached_and_new_scheduler_computed_positions_are_authoritative(self):
        for source in ("cached", "new"):
            for broadcast, local, expected in ((7, 100, None), (8, -100, ("r",))):
                with self.subTest(source=source, broadcast=broadcast, local=local):
                    rows = [("r", broadcast)]
                    output = scheduler(cached=rows if source == "cached" else [],
                                       new=rows if source == "new" else [])
                    self.assertEqual(self.eligible(request(num_computed_tokens=local), output), expected)

    def test_new_scheduler_row_overrides_duplicate_cached_row(self):
        # Documents selector precedence only, not scheduler duplicate validity.
        for cached, new, expected in ((7, 8, ("r",)), (8, 7, None)):
            with self.subTest(cached=cached, new=new):
                output = scheduler(cached=[("r", cached)], new=[("r", new)])
                self.assertEqual(self.eligible(output=output), expected)

    def test_unknown_request_or_missing_broadcast_position_falls_back(self):
        self.assertIsNone(mode.plain_decode_request_ids(scheduler(), {}))
        self.assertIsNone(self.eligible(output=scheduler(cached=[])))
        output = scheduler(cached=[])
        output.scheduled_cached_reqs.req_ids = ["r"]
        self.assertIsNone(self.eligible(output=output))

    def test_scheduler_level_exclusions(self):
        for field, value in (
            ("total_num_scheduled_tokens", 0),
            ("has_structured_output_requests", True),
            ("pending_structured_output_tokens", True),
            ("scheduled_spec_decode_tokens", {"r": [7]}),
            ("scheduled_encoder_inputs", {"r": [0]}),
        ):
            with self.subTest(field=field):
                self.assertIsNone(self.eligible(output=scheduler(**{field: value})))
        self.assertIsNone(self.eligible(output=scheduler(scheduled={})))
        self.assertIsNone(self.eligible(output=scheduler(scheduled={}, total_num_scheduled_tokens=1)))

    def test_guard_ids_are_sorted_not_model_row_order(self):
        output = scheduler(scheduled={"z": 1, "a": 1}, cached=[("a", 8), ("z", 8)])
        requests = {"z": request(), "a": request(), "unscheduled": request()}
        self.assertEqual(mode.plain_decode_request_ids(output, requests), ("a", "z"))
        self.assertEqual(tuple(output.num_scheduled_tokens), ("z", "a"))


class PlanScopeTests(unittest.TestCase):
    def setUp(self):
        self.assertIs(mode.current_logits_plan(), mode.FULL_PLAN)

    def tearDown(self):
        self.assertIs(mode.current_logits_plan(), mode.FULL_PLAN)

    def test_nested_scope_restores_exact_outer_plan(self):
        outer = mode.BatchSamplingPlan(mode.SamplingMode.COMPACT_GREEDY, ("r",), (object(),))
        inner = mode.BatchSamplingPlan(mode.SamplingMode.FULL, ("other",), (object(),))
        with mode.logits_plan_scope(outer):
            self.assertIs(mode.current_logits_plan(), outer)
            with mode.logits_plan_scope(inner):
                self.assertIs(mode.current_logits_plan(), inner)
            self.assertIs(mode.current_logits_plan(), outer)

    def test_nested_exception_restores_outer_then_default(self):
        outer = mode.BatchSamplingPlan(mode.SamplingMode.COMPACT_GREEDY)
        inner = mode.BatchSamplingPlan(mode.SamplingMode.FULL)
        with self.assertRaisesRegex(RuntimeError, "outer"):
            with mode.logits_plan_scope(outer):
                with self.assertRaisesRegex(ValueError, "inner"):
                    with mode.logits_plan_scope(inner):
                        raise ValueError("inner")
                self.assertIs(mode.current_logits_plan(), outer)
                raise RuntimeError("outer")

    def test_plan_is_immutable_snapshot(self):
        plan = mode.BatchSamplingPlan(mode.SamplingMode.COMPACT_GREEDY, ("r",), (object(),))
        with self.assertRaises(FrozenInstanceError):
            plan.mode = mode.SamplingMode.FULL
        self.assertEqual(len(plan.request_states), 1)


def load_actual_plan_builder():
    """Execute only the real method body, never the runtime module imports."""
    path = SOURCE_ROOT / "vllm_ascend/worker/model_runner_v1.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef) and node.name == "_compact_sampling_plan"]
    if len(matches) != 1:
        raise AssertionError("Expected exactly one real _compact_sampling_plan method")
    isolated = ast.Module(body=[ast.ImportFrom(module="__future__", names=[
        ast.alias(name="annotations")], level=0), matches[0]], type_ignores=[])
    ast.fix_missing_locations(isolated)
    namespace = dict(FULL_PLAN=mode.FULL_PLAN, BatchSamplingPlan=mode.BatchSamplingPlan,
                     SamplingMode=mode.SamplingMode,
                     plain_decode_request_ids=mode.plain_decode_request_ids)
    exec(compile(isolated, str(path), "exec"), namespace)
    return namespace["_compact_sampling_plan"]


def load_actual_sampling_guard():
    """Extract the exact fail-closed predicate and raise, not a copied guard."""
    path = SOURCE_ROOT / "vllm_ascend/worker/model_runner_v1.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    message = "compact sampling execution/request contract changed before sampling"
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
               and any(isinstance(stmt, ast.Raise)
                       and any(isinstance(value, ast.Constant) and value.value == message
                               for value in ast.walk(stmt)) for stmt in node.body)]
    if len(matches) != 1:
        raise AssertionError("Expected exactly one sampling contract guard")
    isolated = ast.parse(
        "def guard(self, sampling_plan, grammar_output=None, spec_decode_metadata=None):\n"
        "    pass\n"
    )
    isolated.body[0].body = [matches[0]]
    ast.fix_missing_locations(isolated)
    namespace = {}
    exec(compile(isolated, str(path), "exec"), namespace)
    return namespace["guard"]


class RequestStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_plan = staticmethod(load_actual_plan_builder())
        cls.check_sampling_guard = staticmethod(load_actual_sampling_guard())

    def make_runner(self):
        return NS(
            _compact_greedy_supported=True,
            requests={"z": request(), "a": request()},
            input_batch=NS(req_ids=["z", "a"]),
            _compact_projector=object(),
            _compact_lm_head=NS(shard_indices=NS(org_vocab_start_index=128),
                                num_org_embeddings_per_partition=128),
        )

    def output(self):
        return scheduler(scheduled={"z": 1, "a": 1}, cached=[("z", 8), ("a", 8)])

    def test_actual_builder_and_guard_preserve_model_row_order(self):
        runner = self.make_runner()
        plan = self.build_plan(runner, self.output())
        self.assertIs(plan.mode, mode.SamplingMode.COMPACT_GREEDY)
        self.assertEqual(plan.request_ids, ("z", "a"))
        self.assertIs(plan.request_states[0], runner.requests["z"])
        self.assertIs(plan.request_states[1], runner.requests["a"])
        self.assertEqual(plan.projector_identity, id(runner._compact_projector))
        self.assertEqual((plan.local_vocab_start, plan.local_vocab_size), (128, 128))
        self.check_sampling_guard(runner, plan)
        runner.input_batch.req_ids = ["a", "z"]
        with self.assertRaisesRegex(RuntimeError, "contract changed"):
            self.check_sampling_guard(runner, plan)
        for rows in (["z"], ["z", "a", "extra"], ["z", "z"]):
            with self.subTest(rows=rows):
                runner.input_batch.req_ids = rows
                with self.assertRaisesRegex(RuntimeError, "rows differ"):
                    self.build_plan(runner, self.output())

    def test_plan_strong_reference_retains_replaced_request_until_retirement(self):
        runner = self.make_runner()
        old_ref = weakref.ref(runner.requests["a"])
        plan = self.build_plan(runner, self.output())
        runner.requests["a"] = request()
        gc.collect()
        # Only the plan retains the old state: no test-owned strong reference
        # or assumption about allocator/id reuse protects this assertion.
        self.assertIsNotNone(old_ref())
        self.assertIs(plan.request_states[1], old_ref())
        self.assertIsNot(plan.request_states[1], runner.requests["a"])
        self.assertEqual(plan.request_states[1], runner.requests["a"])
        with self.assertRaisesRegex(RuntimeError, "contract changed"):
            self.check_sampling_guard(runner, plan)
        del plan
        gc.collect()
        self.assertIsNone(old_ref())

    def test_request_states_use_identity_not_mutation_epoch_or_plan_equality(self):
        runner = self.make_runner()
        first = self.build_plan(runner, self.output())
        runner.requests["a"].num_computed_tokens = 999
        second = self.build_plan(runner, self.output())
        self.assertIs(first.request_states[1], second.request_states[1])
        self.check_sampling_guard(runner, first)
        self.assertNotIn("request_states", repr(first))
        different_states = replace(first, request_states=(request(), request()))
        # compare=False intentionally excludes states from dataclass equality;
        # the real sampling guard must still reject distinct objects.
        self.assertEqual(first, different_states)
        with self.assertRaisesRegex(RuntimeError, "contract changed"):
            self.check_sampling_guard(runner, different_states)

    def test_actual_builder_full_fallback_does_not_capture_request_states(self):
        runner = self.make_runner()
        runner._compact_greedy_supported = False
        self.assertIs(self.build_plan(runner, self.output()), mode.FULL_PLAN)
        runner._compact_greedy_supported = True
        runner.requests["a"].sampling_params.logprobs = 0
        self.assertIs(self.build_plan(runner, self.output()), mode.FULL_PLAN)


if __name__ == "__main__":
    unittest.main()
