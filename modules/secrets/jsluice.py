import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class JsluiceModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['sh', '-c', f'jsluice urls -R {target} > {container_out}']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'jsluice.json')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(f"https://{target}", container_out))
        
        try:
            data = json.loads(self._read_output_file(host_out))
            count = len(data) if isinstance(data, list) else 1
        except (EmptyOutputError, json.JSONDecodeError):
            count = 0
            
        return {'results': [], 'count': count, 'requests_made': 50}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('js_secrets_found', confidence='high', source='jsluice')
