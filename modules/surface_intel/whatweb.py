import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError, OutputParseError

class WhatWebModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['whatweb', target, '--log-json', container_out]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        # Determine if we have a live web list or just a domain
        host_input_file = os.path.join(output_dir, 'raw', 'httpx.json')
        container_input_file = f"/{host_input_file.replace('\\', '/')}"
        
        host_output_file = os.path.join(output_dir, 'raw', 'whatweb.json')
        container_output_file = f"/{host_output_file.replace('\\', '/')}" 
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        if os.path.exists(host_input_file):
            command = ['whatweb', '--input-file', container_input_file, '--log-json', container_output_file]
        else:
            command = self.build_command(target, container_output_file)
            
        self._run_subprocess(command)

        try:
            content = self._read_output_file(host_output_file)
            results = json.loads(content)
        except (EmptyOutputError, json.JSONDecodeError):
            results = []

        return {
            'results':       results,
            'count':         len(results),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_tech_intel', confidence='high', source='whatweb')

    def estimated_requests(self) -> int:
        return 50 # Single target is light, file input is handled internally without a tight predictable loop
