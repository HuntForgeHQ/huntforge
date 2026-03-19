import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class DirsearchModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # We need a specific URL for dirsearch
        return ['dirsearch', '-u', f'https://{target}', '-o', container_out, '-q', '--no-color', '--format', 'json']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'dirsearch.json')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        try:
            content = self._read_output_file(host_out)
            results = len(content.splitlines()) # Just counting paths found for now
        except EmptyOutputError:
            results = 0
            
        return {'results': [], 'count': results, 'requests_made': 5000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('hidden_paths_found', confidence='high', source='dirsearch')
