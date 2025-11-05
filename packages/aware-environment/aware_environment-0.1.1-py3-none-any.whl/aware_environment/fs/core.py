"""Plan executor for kernel-driven filesystem operations."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, MutableMapping, Optional, Protocol, Sequence

from aware_file_system.operations import ensure_directory as _ensure_directory
from aware_file_system.operations import move_path as _move_path
from aware_file_system.operations import write_file as _write_file

from ..frontmatter import load_frontmatter
from .receipt import (
    HookLog,
    OperationContext,
    PolicyDecision,
    Receipt,
    EnsureOp,
    MoveOp,
    WriteOp,
)


class OperationWritePolicy(str, Enum):
    """Supported write policies for journal execution."""

    WRITE_ONCE = "write_once"
    APPEND_ENTRY = "append_entry"
    MODIFIABLE = "modifiable"


@dataclass(frozen=True)
class EnsureInstruction:
    """Instruction to ensure a directory exists."""

    path: Path


@dataclass(frozen=True)
class MoveInstruction:
    """Instruction to move a path to a new destination."""

    src: Path
    dest: Path
    overwrite: bool = False


@dataclass(frozen=True)
class WriteInstruction:
    """Instruction describing a file write governed by a policy."""

    path: Path
    content: str
    policy: OperationWritePolicy
    event: str
    doc_type: str
    timestamp: datetime
    metadata: Mapping[str, object]
    hook_metadata: Mapping[str, object] = field(default_factory=dict)
    open_after: bool = False


@dataclass(frozen=True)
class OperationPlan:
    """Aggregated plan produced by kernel handlers."""

    context: OperationContext
    ensure_dirs: Sequence[EnsureInstruction] = field(default_factory=tuple)
    moves: Sequence[MoveInstruction] = field(default_factory=tuple)
    writes: Sequence[WriteInstruction] = field(default_factory=tuple)


class PolicyAdapter(Protocol):
    """Protocol describing the policy enforcement contract."""

    def guard_create(self, path: Path, *, force: bool = False) -> None:  # pragma: no cover - interface
        ...

    def guard_append(self, path: Path) -> None:  # pragma: no cover - interface
        ...

    def guard_modify(self, path: Path) -> None:  # pragma: no cover - interface
        ...

    def build_receipt(self, action: str, path: Path, metadata: Mapping[str, object] | None = None) -> object: ...

    def run_hooks(self, receipt: object) -> None:  # pragma: no cover - interface
        ...


PolicyProvider = Callable[[WriteInstruction], PolicyAdapter]
EnsureCallback = Callable[[Path], object | None]
MoveCallback = Callable[[Path, Path, bool], object | None]
WriteCallback = Callable[[Path, str, bool], object | None]


@dataclass
class _DefaultPolicyAdapter:
    """Fallback policy adapter used when no external enforcer is supplied."""

    policy: OperationWritePolicy

    def guard_create(self, path: Path, *, force: bool = False) -> None:
        if self.policy is OperationWritePolicy.WRITE_ONCE and path.exists() and not force:
            raise FileExistsError(f"{path} already exists; use force=True or migrate policy to allow overwrite.")

    def guard_append(self, path: Path) -> None:
        if self.policy is not OperationWritePolicy.APPEND_ENTRY:
            raise PermissionError("Append operations are not permitted for this policy.")

    def guard_modify(self, path: Path) -> None:
        if self.policy is not OperationWritePolicy.MODIFIABLE:
            raise PermissionError("Modify operations are not permitted for this policy.")

    def build_receipt(self, action: str, path: Path, metadata: Mapping[str, object] | None = None) -> object:
        return {
            "action": action,
            "path": str(path),
            "policy": self.policy.value,
            "metadata": dict(metadata or {}),
        }

    def run_hooks(self, receipt: object) -> None:  # pragma: no cover - no hooks by default
        return


def _resolve_policy_adapter(
    instruction: WriteInstruction,
    policy_provider: PolicyProvider | None,
) -> PolicyAdapter:
    if policy_provider is not None:
        return policy_provider(instruction)
    return _DefaultPolicyAdapter(instruction.policy)


def _execute_write_instruction(
    instruction: WriteInstruction,
    *,
    dry_run: bool,
    force: bool,
    policy_adapter: PolicyAdapter,
    write_callback: WriteCallback,
    open_callback: Callable[[Path], None] | None,
) -> tuple[WriteOp | None, list[PolicyDecision]]:
    path = instruction.path
    exists = path.exists()

    decisions: list[PolicyDecision] = []

    def _allow(action: str) -> None:
        decisions.append(
            PolicyDecision(
                path=path,
                action=action,  # type: ignore[arg-type]
                policy=instruction.policy.value,
                result="allow",
            )
        )

    if instruction.policy is OperationWritePolicy.WRITE_ONCE:
        policy_adapter.guard_create(path, force=force)
        _allow("guard_create")
    elif instruction.policy is OperationWritePolicy.APPEND_ENTRY:
        if exists:
            policy_adapter.guard_append(path)
            _allow("guard_append")
        else:
            policy_adapter.guard_create(path, force=force)
            _allow("guard_create")
    else:  # MODIFIABLE
        if exists:
            policy_adapter.guard_modify(path)
            _allow("guard_modify")
        else:
            policy_adapter.guard_create(path, force=force)
            _allow("guard_create")

    if dry_run:
        return None, decisions

    write_callback(path, instruction.content, True)

    frontmatter = load_frontmatter(path)
    metadata: MutableMapping[str, object] = dict(frontmatter.metadata)
    metadata.setdefault("updated", instruction.timestamp.isoformat())

    receipt = policy_adapter.build_receipt(instruction.event, path, instruction.hook_metadata)
    policy_adapter.run_hooks(receipt)

    content_hash = hashlib.sha256(instruction.content.encode("utf-8")).hexdigest()
    write_op = WriteOp(
        path=path,
        event=instruction.event,  # type: ignore[arg-type]
        policy=instruction.policy.value,
        doc_type=instruction.doc_type,
        content_hash=f"sha256:{content_hash}",
        metadata=dict(metadata),
        hook_metadata=dict(instruction.hook_metadata),
        timestamp=instruction.timestamp,
    )

    if instruction.open_after and open_callback is not None:
        open_callback(path)

    return write_op, decisions


def apply_plan(
    plan: OperationPlan,
    *,
    dry_run: bool = False,
    force: bool = False,
    policy_provider: PolicyProvider | None = None,
    ensure_callback: EnsureCallback | None = None,
    move_callback: MoveCallback | None = None,
    write_callback: WriteCallback | None = None,
    open_callback: Callable[[Path], None] | None = None,
) -> Receipt:
    """Execute the supplied operation plan and return a structured receipt."""

    ensure_impl = ensure_callback or (lambda path: _ensure_directory(path))
    move_impl = move_callback or (lambda src, dst, overwrite: _move_path(src, dst, overwrite=overwrite))
    write_impl = write_callback or (lambda path, content, overwrite: _write_file(path, content, overwrite=overwrite))

    receipt = Receipt(
        receipt_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        context=OperationContext(
            object_type=plan.context.object_type,
            function=plan.context.function,
            selectors=dict(plan.context.selectors),
        ),
    )

    for instruction in plan.ensure_dirs:
        if not dry_run:
            ensure_impl(instruction.path)
            receipt.add_fs_op(EnsureOp(path=instruction.path))

    for instruction in plan.moves:
        if dry_run:
            continue
        move_impl(instruction.src, instruction.dest, instruction.overwrite)
        receipt.add_fs_op(
            MoveOp(
                src=instruction.src,
                dest=instruction.dest,
                overwrite=instruction.overwrite,
            )
        )

    for instruction in plan.writes:
        adapter = _resolve_policy_adapter(instruction, policy_provider)
        write_op, decisions = _execute_write_instruction(
            instruction,
            dry_run=dry_run,
            force=force,
            policy_adapter=adapter,
            write_callback=write_impl,
            open_callback=open_callback,
        )
        for decision in decisions:
            receipt.add_policy_decision(decision)
        if write_op is not None:
            receipt.add_fs_op(write_op)

    return receipt


__all__ = [
    "OperationWritePolicy",
    "OperationContext",
    "Receipt",
    "EnsureOp",
    "MoveOp",
    "WriteOp",
    "EnsureInstruction",
    "MoveInstruction",
    "WriteInstruction",
    "OperationPlan",
    "PolicyAdapter",
    "PolicyProvider",
    "apply_plan",
]
