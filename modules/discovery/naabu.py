import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError, OutputParseError

class NaabuModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['naabu', '-host', target, '-o', container_out, '-silent']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'naabu.txt')
        container_output_file = f"/{host_output_file.replace('\\', '/')}" 
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        command = self.build_command(target, container_output_file)
        
        if self._cfg('top_ports'):
            command += ['-top-ports', str(self._cfg('top_ports'))]
            
        self._run_subprocess(command)

        try:
            content = self._read_output_file(host_output_file)
            ports = [p.strip() for p in content.splitlines() if p.strip()]
        except EmptyOutputError:
            ports = []

        return {
            'results':       ports,
            'count':         len(ports),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_open_ports', confidence='high', evidence=result['results'][:5], source='naabu')

    def estimated_requests(self) -> int:
        return 1000 # SYN scan is relatively heavy
