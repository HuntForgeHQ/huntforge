import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError, OutputParseError

class DnsxModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['dnsx', '-o', container_out, '-json', '-silent']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_input_file = os.path.join(output_dir, 'raw', 'subfinder.txt')
        container_input_file = f"/{host_input_file.replace('\\', '/')}"
        
        if not os.path.exists(host_input_file):
            return {'results': [], 'count': 0, 'requests_made': 0}
            
        host_output_file = os.path.join(output_dir, 'raw', 'dnsx.json')
        container_output_file = f"/{host_output_file.replace('\\', '/')}" 
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        command = self.build_command(target, container_output_file)
        command += ['-l', container_input_file]
        
        self._run_subprocess(command)

        try:
            content = self._read_output_file(host_output_file)
            results = []
            for line in content.splitlines():
                if line.strip():
                    results.append(json.loads(line))
        except EmptyOutputError:
            results = []

        return {
            'results':       results,
            'count':         len(results),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_resolved_dns', confidence='high', source='dnsx')
            
            cnames = [r.get('cname') for r in result['results'] if r.get('cname')]
            if cnames:
                tag_manager.add('has_cnames', confidence='high', source='dnsx')

    def estimated_requests(self) -> int:
        return 200
