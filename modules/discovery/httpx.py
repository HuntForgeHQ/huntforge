import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError, OutputParseError

class HttpxModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        # httpx takes a list of targets. When orchestrator passes 'example.com', 
        # normally we should pass a file of subdomains. But per methodology, httpx runs after subfinder.
        # We will assume target is the domain, and the orchestrator or `run` method supplies the input file.
        # Actually, let's configure `run` so input is the `subfinder.txt`
        cmd = ['httpx', '-o', container_out, '-json', '-silent']
        
        # We process input file in `run()`
        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        # Input file from subfinder or merged Phase 1 output
        host_input_file = os.path.join(output_dir, 'processed', 'all_subdomains.txt')
        if not os.path.exists(host_input_file):
            host_input_file = os.path.join(output_dir, 'raw', 'subfinder.txt')
            
        container_input_file = host_input_file.replace('\\', '/')
        
        if not os.path.exists(host_input_file):
            return {'results': [], 'count': 0, 'requests_made': 0}
            
        host_output_file = os.path.join(output_dir, 'raw', 'httpx.json')
        container_output_file = host_output_file.replace('\\', '/')
        
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        command = self.build_command(target, container_output_file)
        command += ['-l', container_input_file]
        
        if self._cfg('ports'):
            command += ['-p', self._cfg('ports')]
            
        self._run_subprocess(command, output_file=host_output_file)

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
        if result['count'] == 0:
            return
            
        urls = [r.get('url') for r in result['results'] if r.get('url')]
        tag_manager.add('has_live_web', confidence='high', evidence=urls[:5], source='httpx')
        
        # Detect tech and WAF
        waf_signatures = ['akamai', 'cloudflare', 'imperva', 'incapsula', 'sucuri', 'aws', 'cloudfront', 'fastly']
        for r in result['results']:
            tech = r.get('tech', [])
            webserver = str(r.get('webserver', '')).lower()
            
            for t in tech:
                t_low = str(t).lower()
                if 'wordpress' in t_low:
                    tag_manager.add('has_wordpress', confidence='high', source='httpx')
                for waf in waf_signatures:
                    if waf in t_low:
                        tag_manager.add('has_waf', confidence='high', source='httpx', evidence=[waf])
            
            for waf in waf_signatures:
                if waf in webserver:
                    tag_manager.add('has_waf', confidence='high', source='httpx', evidence=[waf])

    def estimated_requests(self) -> int:
        return 500
