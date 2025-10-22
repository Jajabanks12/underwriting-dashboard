from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import ast
import operator as op
import yaml
from pathlib import Path

ALLOWED_BINOPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
ALLOWED_CMPOPS = {
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Gt: op.gt,
    ast.GtE: op.ge,
}
ALLOWED_BOOL = {ast.And: all, ast.Or: any}
ALLOWED_UNARY = {ast.USub: op.neg, ast.UAdd: op.pos, ast.Not: op.not_}


@dataclass
class RuleResult:
    id: str
    description: str
    severity: str
    passed: bool
    detail: str


def _eval(node: ast.AST, ctx: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise KeyError(f"Unknown name: {node.id}")
        return ctx[node.id]
    if isinstance(node, ast.Subscript):  # e.g., d['x']
        val = _eval(node.value, ctx)
        key = (
            _eval(node.slice, ctx) if isinstance(node.slice, ast.Index) else _eval(node.slice, ctx)
        )
        return val[key]
    if isinstance(node, ast.List):
        return [_eval(e, ctx) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e, ctx) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {_eval(k, ctx): _eval(v, ctx) for k, v in zip(node.keys, node.values)}

    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
        return ALLOWED_UNARY[type(node.op)](_eval(node.operand, ctx))

    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        return ALLOWED_BINOPS[type(node.op)](_eval(node.left, ctx), _eval(node.right, ctx))

    if isinstance(node, ast.Compare):
        left = _eval(node.left, ctx)
        for opnode, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, ctx)
            if type(opnode) not in ALLOWED_CMPOPS or not ALLOWED_CMPOPS[type(opnode)](left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.BoolOp) and type(node.op) in ALLOWED_BOOL:
        vals = [_eval(v, ctx) for v in node.values]
        # Normalize truthiness for 'all'/'any'
        if isinstance(node.op, ast.And):
            return all(bool(v) for v in vals)
        if isinstance(node.op, ast.Or):
            return any(bool(v) for v in vals)

    if isinstance(node, ast.Call):
        # Allow only certain built-ins used in our examples: max, min, len
        fn = _eval(node.func, ctx)
        if fn not in (max, min, len):
            raise ValueError("Function calls are restricted")
        args = [_eval(a, ctx) for a in node.args]
        return fn(*args)

    if isinstance(node, ast.Attribute):
        val = _eval(node.value, ctx)
        return getattr(val, node.attr)

    if isinstance(node, ast.NameConstant):  # Py<3.8 legacy
        return node.value

    if isinstance(node, ast.Name) and node.id in ("True", "False", "None"):
        return {"True": True, "False": False, "None": None}[node.id]

    raise ValueError(f"Disallowed expression: {ast.dump(node)}")


def safe_eval(expr: str, context: Dict[str, Any]) -> Any:
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body, {**context, "max": max, "min": min, "len": len})


def load_rules(path: Path) -> Tuple[str, List[dict]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("version", "0.0.0"), data.get("rules", [])


def build_context(payload: dict) -> Dict[str, Any]:
    # Flatten nested fields for convenience
    addr = payload.get("address") or {}
    ctx = dict(payload)
    ctx["city"] = addr.get("city")
    ctx["state"] = addr.get("state")
    ctx["zip"] = addr.get("zip")
    return ctx


def evaluate_rules(payload: dict, rules_path: Path) -> Dict[str, Any]:
    version, rules = load_rules(rules_path)
    ctx = build_context(payload)
    results: List[RuleResult] = []
    counts = {"passed": 0, "failed": 0}
    for r in rules:
        cid = r["condition"]
        try:
            ok = bool(safe_eval(cid, ctx))
            detail = "OK" if ok else "Condition evaluated to False"
        except Exception as e:
            ok = False
            detail = f"Error: {e!s}"
        results.append(
            RuleResult(
                id=r["id"],
                description=r.get("description", ""),
                severity=r.get("severity", "info"),
                passed=ok,
                detail=detail,
            )
        )
        counts["passed" if ok else "failed"] += 1

    return {
        "rules_version": version,
        "results": [rr.__dict__ for rr in results],
        "summary": counts,
    }
