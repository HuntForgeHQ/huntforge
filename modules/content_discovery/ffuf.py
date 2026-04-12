import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class FfufModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        wl_config = self._cfg('wordlist', '~/.huntforge/wordlists/directories/raft-medium-words.txt')
        wl = os.path.expanduser(wl_config)
        if not os.path.exists(wl):
            wl = '/usr/share/dirb/wordlists/common.txt'
            
        cmd = ['ffuf', '-u', f'https://{target}/FUZZ', '-w', wl, '-o', container_out, '-of', 'json', '-s']
        
        match_codes = self._cfg('match_codes')
        if match_codes:
            cmd.extend(['-mc', str(match_codes)])
        cmd.append('-ac') # Auto-calibrate is usually good
        
        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, live_hosts: str = None, all_urls: str = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'ffuf.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        # It's better if we run ffuf on the domain or live hosts file. Default to domain for simplicity here.
        self._run_subprocess(self.build_command(target, container_out), output_file=host_out)
        
        try:
            content = json.loads(self._read_output_file(host_out))
            results = content.get('results', [])
        except (EmptyOutputError, json.JSONDecodeError):
            results = []
            
        return {'results': results, 'count': len(results), 'requests_made': 5000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            paths = [r.get('url', '') for r in result['results']]
            if any('admin' in p.lower() for p in paths):
                tag_manager.add('admin_panel_found', confidence='high', source='ffuf')
            if any('.bak' in p.lower() or '.zip' in p.lower() for p in paths):
                tag_manager.add('backup_files_found', confidence='high', source='ffuf')
