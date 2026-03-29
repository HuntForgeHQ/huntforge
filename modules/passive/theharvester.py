import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class TheHarvesterModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['theHarvester', '-d', target, '-b', 'all', '-l', '500', '-f', container_out]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'theharvester.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        try:
            content = self._read_output_file(host_out)
            # The tool outputs interesting logic, we just count finding length here
            results = 1 if len(content) > 50 else 0
        except EmptyOutputError:
            results = 0
            
        return {'results': [], 'count': results, 'requests_made': 100}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('osint_data_found', confidence='medium', source='theharvester')
