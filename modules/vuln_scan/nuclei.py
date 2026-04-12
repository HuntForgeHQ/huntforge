import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class NucleiModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        cmd = ['nuclei', '-target', target, '-json-export', container_out, '-silent']
        
        severity = self._cfg('severity')
        if severity:
            cmd += ['-severity', severity]
            
        tags = self._cfg('tags')
        if tags:
            cmd += ['-tags', tags]
            
        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_input_file = os.path.join(output_dir, 'raw', 'httpx.json')
        container_input_file = host_input_file.replace('\\', '/')
        
        host_output_file = os.path.join(output_dir, 'raw', 'nuclei.json')
        container_output_file = host_output_file.replace('\\', '/')
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        # If live web targets exist, use them. Otherwise scan the raw domain.
        if os.path.exists(host_input_file) and not self._cfg('force_domain_only'):
            command = ['nuclei', '-l', container_input_file, '-json-export', container_output_file, '-silent']
            severity = self._cfg('severity')
            if severity:
                command += ['-severity', severity]
            tags = self._cfg('tags')
            if tags:
                command += ['-tags', tags]
        else:
            command = self.build_command(target, container_output_file)
            
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
        if result['count'] > 0:
            tag_manager.add('has_vulnerabilities', confidence='high', source='nuclei')
            
            severities = [
                r.get('info', {}).get('severity') 
                for r in result['results'] 
                if isinstance(r, dict)
            ]
            if any(s in ['critical', 'high'] for s in severities):
                tag_manager.add('has_critical_vulns', confidence='high', source='nuclei')

    def estimated_requests(self) -> int:
        return 15000 # Nuclei is intensely heavy; set a high budget estimate.
