import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class TrufflehogModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # trufflehog github --org target --json > file
        return ['sh', '-c', f'trufflehog github --org={target} --json > {container_out}']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'trufflehog.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        try:
            self._run_subprocess(self.build_command(target, container_out))
        except Exception as e:
            if 'exited with code 1' not in str(e): raise
            
        try:
            subs = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            subs = []
            
        return {'results': subs, 'count': len(subs), 'requests_made': 50}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('leaked_credentials', confidence='high', source='trufflehog')
