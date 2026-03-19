import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class PurednsModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return []

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'puredns.txt')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        subfinder_file = os.path.join(output_dir, 'raw', 'subfinder.txt')
        cont_in = f"/{subfinder_file.replace('\\', '/')}"
        
        if os.path.exists(subfinder_file):
            cmd = ['puredns', 'resolve', cont_in, '-o', container_out, '--wildcard-tests', '30']
            self._run_subprocess(cmd)
        
        try:
            subs = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            subs = []
            
        return {'results': subs, 'count': len(subs), 'requests_made': 5000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_resolved_dns', confidence='high', source='puredns')
