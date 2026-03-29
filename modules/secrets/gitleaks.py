import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class GitleaksModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # gitleaks detect --source /output/example.com --report-path container_out --no-git
        source_dir = f"output/{target}"
        return ['gitleaks', 'detect', '--source', source_dir, '--report-path', container_out, '--no-git', '-v']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'gitleaks.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        # We don't fail if the tool exit code is 1 (gitleaks returns 1 if leaks found)
        # We must intercept it by calling docker_runner directly, or since BaseModule._run_subprocess 
        # raises ToolExecutionError, we can subclass or just catch it.
        try:
            self._run_subprocess(self.build_command(target, container_out))
        except Exception as e:
            # gitleaks exit code 1 = leaks present
            if 'exited with code 1' not in str(e):
                raise
                
        try:
            content = self._read_output_file(host_out)
            leaks = json.loads(content)
            if not isinstance(leaks, list): leaks = []
        except (EmptyOutputError, json.JSONDecodeError):
            leaks = []
            
        return {'results': leaks, 'count': len(leaks), 'requests_made': 10}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('leaked_credentials', confidence='high', source='gitleaks')
