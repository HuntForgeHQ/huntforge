import os
import shutil
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class ParamspiderModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # paramspider outputs to ./results/<domain>.txt by default (no -o flag)
        # Use the venv binary directly
        return ['/home/huntforge/venv/bin/paramspider', '-d', target]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'paramspider.txt')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        # paramspider writes output to ./results/<domain>.txt automatically
        # We run it and then copy the output to our expected location
        self._run_subprocess(self.build_command(target, host_out), output_file=host_out)
        
        # paramspider saves results to ./results/<domain>.txt
        default_output = os.path.join('results', f'{target}.txt')
        if os.path.exists(default_output):
            shutil.copy(default_output, host_out)
        
        try:
            urls = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            urls = []
            
        return {'results': urls, 'count': len(urls), 'requests_made': 20}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('params_found', confidence='high', source='paramspider')
