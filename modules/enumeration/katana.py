import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class KatanaModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['katana', '-u', f'https://{target}', '-o', container_out, '-silent', '-jsonl']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'katana.jsonl')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        try:
            content = self._read_output_file(host_out)
            urls = []
            for line in content.splitlines():
                if line.strip():
                    try:
                        urls.append(json.loads(line).get('endpoint', ''))
                    except:
                        pass
        except EmptyOutputError:
            urls = []
            
        return {'results': urls, 'count': len(urls), 'requests_made': 1000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('api_endpoints_found', confidence='medium', source='katana')
