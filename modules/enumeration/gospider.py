import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class GospiderModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['gospider', '-s', f'https://{target}', '-o', container_out, '-c', '10', '-d', '3', '-q']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        # Gospider outputs to a directory named after the domain
        host_out = os.path.join(output_dir, 'raw', 'gospider')
        container_out = host_out.replace('\\', '/')
        os.makedirs(host_out, exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        # Check files within the output directory
        count = 0
        try:
            for root, dirs, files in os.walk(host_out):
                for file in files:
                    with open(os.path.join(root, file), 'r') as f:
                        count += len(f.readlines())
        except:
            count = 0
            
        return {'results': [], 'count': count, 'requests_made': 1000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('api_endpoints_found', confidence='high', source='gospider')
