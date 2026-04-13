import os
import shutil
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError, BinaryNotFoundError

_PARAMSPIDER_FALLBACK_PATHS = [
    '/home/huntforge/venv/bin/paramspider',
    '/usr/local/bin/paramspider',
    '/usr/bin/paramspider',
    os.path.expanduser('~/.local/bin/paramspider'),
]


def _find_paramspider() -> str:
    found = shutil.which('paramspider')
    if found:
        return found
    for path in _PARAMSPIDER_FALLBACK_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise BinaryNotFoundError(
        "paramspider binary not found on PATH or in common locations. "
        "Install it with: pip install paramspider",
        tool='paramspider',
    )


class ParamspiderModule(BaseModule):
    def build_command(self, target: str, output_file: str) -> list:
        return [_find_paramspider(), '-d', target]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'paramspider.txt')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        self._run_subprocess(self.build_command(target, host_out), output_file=host_out)

        default_output = os.path.join('results', f'{target}.txt')
        if os.path.exists(default_output):
            shutil.copy2(default_output, host_out)

        try:
            urls = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            urls = []

        return {'results': urls, 'count': len(urls), 'requests_made': 20}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('params_found', confidence='high', source='paramspider')
