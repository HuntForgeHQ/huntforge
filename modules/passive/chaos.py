import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class ChaosModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # chaos -d target -silent -o container_out
        return ['chaos', '-d', target, '-silent', '-o', container_out]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'chaos.txt')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        cmd = self.build_command(target, container_out)
        api_key = os.environ.get("CHAOS_KEY")
        if api_key:
            cmd.extend(['-key', api_key])
            
        self._run_subprocess(cmd)
        
        try:
            subs = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            subs = []
            
        return {'results': subs, 'count': len(subs), 'requests_made': 5}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_subdomains', confidence='high', source='chaos')
