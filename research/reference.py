"""Exact rational model of bounded candidate recovery; not a device sampler."""

from fractions import Fraction

VERSION = "reference-0.1.0"


def validate(shards, p):
    if isinstance(p, bool) or not isinstance(p, (int, Fraction)) or not 0 < p <= 1:
        raise ValueError("p must be an exact rational in (0, 1]")
    rows = [item for shard in shards for item in shard]
    ids = set()
    for token, mass in rows:
        if (
            isinstance(token, bool)
            or not isinstance(token, int)
            or token < 0
            or token in ids
        ):
            raise ValueError("token IDs must be unique nonnegative integers")
        if isinstance(mass, bool) or not isinstance(mass, (int, Fraction)) or mass < 0:
            raise ValueError("masses must be exact nonnegative rationals")
        ids.add(token)
    if not rows or sum(mass for _, mass in rows) == 0:
        raise ValueError("distribution must have positive total mass")
    return rows


def ordered(rows):
    """Tie contract: descending mass, ascending token ID; omit zero mass."""
    return sorted(
        ((token, Fraction(mass)) for token, mass in rows if mass),
        key=lambda item: (-item[1], item[0]),
    )


def prefix(rows, target):
    selected, total = [], Fraction(0)
    for token, mass in rows:
        selected.append((token, mass))
        total += mass
        if total >= target:
            return tuple(selected)
    raise ValueError("insufficient candidate mass")


def bounded_nucleus(shards, p, budgets=(4, 16, 64, 128)):
    """Return exact support and model counters, including full fallback if needed.

    Each round sends at most K positive-mass entries per shard; merging gives
    global top-K. Full-distribution mass is assumed available to the model.
    Counters exclude normalizer/control collectives and are not runtime costs.
    """
    shards = tuple(tuple(shard) for shard in shards)
    rows = validate(shards, p)
    budgets = tuple(budgets)
    if (
        not budgets
        or any(isinstance(k, bool) or not isinstance(k, int) or k < 1 for k in budgets)
        or any(a >= b for a, b in zip(budgets, budgets[1:]))
    ):
        raise ValueError("budgets must be positive, strictly increasing integers")
    target = Fraction(p) * sum(mass for _, mass in rows)
    local = [ordered(shard) for shard in shards]
    transmitted = 0
    for rounds, k in enumerate(budgets, 1):
        sent = [item for shard in local for item in shard[:k]]
        transmitted += len(sent)
        candidates = ordered(sent)[:k]
        if sum(mass for _, mass in candidates) >= target:
            return {
                "support": prefix(candidates, target),
                "fallback": False,
                "candidate_rounds": rounds,
                "candidate_items": transmitted,
                "fallback_items": 0,
            }
    return {
        "support": prefix(ordered(rows), target),
        "fallback": True,
        "candidate_rounds": len(budgets),
        "candidate_items": transmitted,
        "fallback_items": len(rows),
    }


def inverse_cdf(support, u):
    """Exact inverse CDF for an externally supplied uniform rational in [0, 1)."""
    if isinstance(u, bool) or not isinstance(u, (int, Fraction)) or not 0 <= u < 1:
        raise ValueError("u must be an exact rational in [0, 1)")
    rows = validate((support,), 1)
    target = Fraction(u) * sum(mass for _, mass in rows)
    cumulative = Fraction(0)
    for token, mass in rows:
        cumulative += mass
        if cumulative > target:
            return token
    raise AssertionError("unreachable CDF endpoint")
