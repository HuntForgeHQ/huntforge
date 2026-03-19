import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class FindomainModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # findomain --target target --quiet -u container_out
        return ['findomain', '--target', target, '--quiet', '-u', container_out]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'findomain.txt')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        self._run_subprocess(self.build_command(target, container_out))
        
        try:
            subs = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            subs = []
            
        return {'results': subs, 'count': len(subs), 'requests_made': 50}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_subdomains', confidence='high', source='findomain')
