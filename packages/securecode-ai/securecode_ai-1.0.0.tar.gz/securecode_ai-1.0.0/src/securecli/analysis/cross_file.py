"""Cross-file analysis utilities for SecureCLI."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

from ..schemas.findings import Finding


@dataclass
class FunctionNode:
    """Represents a function discovered in repository source code."""

    name: str
    file_path: Path
    start_line: int
    end_line: int
    calls: Set[str]

    @property
    def qualified_name(self) -> str:
        relative = self.file_path.as_posix()
        return f"{relative}:{self.name}"


class _CallGraphVisitor(ast.NodeVisitor):
    """AST visitor that collects function calls within a function body."""

    def __init__(self) -> None:
        self.calls: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:  # type: ignore[override]
        call_name = self._extract_call_name(node.func)
        if call_name:
            self.calls.add(call_name)
        self.generic_visit(node)

    def _extract_call_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


class CrossFileAnalyzer:
    """Builds a lightweight cross-file call graph to enrich findings."""

    def __init__(self, repo_root: Union[str, Path]) -> None:
        self.repo_root = Path(repo_root)
        self._functions_by_file: Dict[Path, List[FunctionNode]] = {}
        self._functions_by_name: Dict[str, List[FunctionNode]] = {}

    def index_repository(self, files: Optional[Iterable[str]] = None) -> None:
        """Parse repository files and populate function/call indexes."""

        if files is None:
            files_to_scan = [p for p in self.repo_root.rglob("*.py")]
        else:
            files_to_scan = [self.repo_root / Path(f) for f in files if f.endswith(".py")]

        for file_path in files_to_scan:
            if not file_path.exists():
                continue
            try:
                source = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                continue

            function_nodes: List[FunctionNode] = []

            for node in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start)
                visitor = _CallGraphVisitor()
                visitor.visit(node)
                func_node = FunctionNode(
                    name=node.name,
                    file_path=file_path,
                    start_line=start,
                    end_line=end,
                    calls=visitor.calls,
                )
                function_nodes.append(func_node)
                self._functions_by_name.setdefault(node.name, []).append(func_node)

            if function_nodes:
                self._functions_by_file[file_path] = function_nodes

    def enrich_findings(self, findings: Iterable[Finding]) -> None:
        """Attach cross-file traces to findings in-place."""

        for finding in findings:
            file_attr = getattr(finding, "file", None)
            if not file_attr:
                continue
            start_line = self._first_line_number(getattr(finding, "lines", ""))
            if start_line is None:
                continue
            file_path = (self.repo_root / file_attr).resolve()
            containing_function = self._find_function(file_path, start_line)
            if not containing_function:
                continue

            trace = self._trace_cross_file_paths(containing_function)
            if trace:
                finding.cross_file = trace

    def _find_function(self, file_path: Path, line_number: int) -> Optional[FunctionNode]:
        functions = self._functions_by_file.get(file_path)
        if not functions:
            return None
        for func in functions:
            if func.start_line <= line_number <= func.end_line:
                return func
        return None

    def _first_line_number(self, line_spec: Optional[str]) -> Optional[int]:
        if not line_spec:
            return None
        try:
            first = str(line_spec).split("-")[0]
            return int(first.strip())
        except (ValueError, AttributeError):
            return None

    def _trace_cross_file_paths(self, root: FunctionNode) -> List[str]:
        visited: Set[str] = set()
        stack: List[Tuple[FunctionNode, List[str]]] = [(root, [root.qualified_name])]
        traces: List[str] = []

        while stack:
            current, path = stack.pop()
            if current.qualified_name in visited:
                continue
            visited.add(current.qualified_name)

            for call in current.calls:
                targets = [
                    fn
                    for fn in self._functions_by_name.get(call, [])
                    if fn.file_path != current.file_path
                ]
                for target in targets:
                    next_path = path + [target.qualified_name]
                    traces.append(" -> ".join(next_path))
                    if len(next_path) < 6:
                        stack.append((target, next_path))

        return traces[:10]


def annotate_cross_file_context(
    repo_root: Union[str, Path],
    findings: Iterable[Finding],
    files: Optional[Iterable[str]] = None,
) -> None:
    """Convenience helper to run cross-file analysis in one call."""

    analyzer = CrossFileAnalyzer(repo_root)
    analyzer.index_repository(files=files)
    analyzer.enrich_findings(findings)
