import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class WappalyzerModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # Assuming we output via sh redirect because wappalyzer cli prints to stdout
        return ['sh', '-c', f'wappalyzer https://{target} > {container_out}']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'wappalyzer.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        try:
            content = self._read_output_file(host_out)
            data = json.loads(content)
            results = data.get('technologies', [])
        except (EmptyOutputError, json.JSONDecodeError):
            results = []
            
        return {'results': results, 'count': len(results), 'requests_made': 10}

    def emit_tags(self, result: dict, tag_manager) -> None:
        for tech in result['results']:
            tech_name = tech.get('name', '').lower()
            if 'wordpress' in tech_name:
                tag_manager.add('has_wordpress', confidence='high', source='wappalyzer')
            if 'aws' in tech_name or 'amazon' in tech_name:
                tag_manager.add('has_cloud_assets', confidence='medium', source='wappalyzer')
