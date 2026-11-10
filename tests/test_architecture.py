"""사용자와 합의한 의존성 경계를 정적 검사로 고정한다."""

import ast
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = {'common': 0, 'domain': 1, 'infrastructure': 2, 'services': 3, 'cli': 4, '__main__': 5}


class ArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = {}
        for path in (ROOT / 'budget_app').rglob('*.py'):
            parts = path.relative_to(ROOT).with_suffix('').parts
            name = '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)
            cls.modules[name] = (path, ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 10)))
        cls.graph = {name: set() for name in cls.modules}
        cls.external = set()
        for name, (path, tree) in cls.modules.items():
            package = name if path.name == '__init__.py' else name.rpartition('.')[0]
            for node in ast.walk(tree):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ''
                    if node.level:
                        base = importlib.util.resolve_name('.' * node.level + base, package)
                    imports = [base] + [base + '.' + alias.name for alias in node.names if base + '.' + alias.name in cls.modules]
                for dependency in imports:
                    if dependency in cls.modules:
                        cls.graph[name].add(dependency)
                    elif dependency:
                        cls.external.add(dependency.split('.')[0])

    def test_only_downward_layer_dependencies(self):
        for source, dependencies in self.graph.items():
            source_layer = source.split('.')[1] if '.' in source else '__main__'
            for target in dependencies:
                target_layer = target.split('.')[1] if '.' in target else '__main__'
                with self.subTest(source=source, target=target):
                    self.assertLessEqual(LAYERS[target_layer], LAYERS[source_layer])
                    if source_layer == 'services':
                        self.assertNotEqual(target_layer, 'services', '기능 서비스끼리 직접 의존하지 않는다.')
                    if source_layer == 'cli':
                        self.assertNotEqual(target_layer, 'infrastructure', 'CLI의 저장소 연결은 진입점이 담당한다.')

    def test_no_import_cycles(self):
        visited = set()
        active = []
        def visit(module):
            self.assertNotIn(module, active, ' -> '.join(active + [module]))
            if module in visited:
                return
            active.append(module)
            for dependency in self.graph[module]:
                visit(dependency)
            active.pop()
            visited.add(module)
        for module in self.graph:
            visit(module)

    def test_lower_layers_have_no_console_io_or_service_file_io(self):
        file_methods = {'open', 'read_text', 'write_text', 'read_bytes', 'write_bytes', 'unlink', 'mkdir'}
        for name, (_, tree) in self.modules.items():
            layer = name.split('.')[1] if '.' in name else '__main__'
            if layer not in ('services', 'infrastructure', 'domain', 'common'):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                with self.subTest(module=name, line=node.lineno):
                    if isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, ('input', 'print'))
                        if layer in ('services', 'domain', 'common'):
                            self.assertNotEqual(node.func.id, 'open')
                    if isinstance(node.func, ast.Attribute) and layer in ('services', 'domain', 'common'):
                        self.assertNotIn(node.func.attr, file_methods)

    def test_only_standard_library_imports(self):
        self.assertEqual(self.external - sys.stdlib_module_names, set())

    def test_source_is_python_310_syntax(self):
        # setUpClass에서 전체 애플리케이션을 3.10 문법으로 파싱했다.
        self.assertGreater(len(self.modules), 20)
