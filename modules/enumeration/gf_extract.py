import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class GfExtractModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return []

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        # GF doesn't make external requests, it greps local files.
        host_out = os.path.join(output_dir, 'raw', 'gf_params.txt')
        container_out = f"/{host_out.replace('\\', '/')}"
        
        gau_file = os.path.join(output_dir, 'raw', 'gau.txt')
        container_in = f"/{gau_file.replace('\\', '/')}"
        
        if os.path.exists(gau_file):
            cmd = ['sh', '-c', f'cat {container_in} | gf params > {container_out}']
            self._run_subprocess(cmd)
        
        try:
            params = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            params = []
            
        return {'results': params, 'count': len(params), 'requests_made': 0}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('params_found', confidence='high', source='gf_extract')
