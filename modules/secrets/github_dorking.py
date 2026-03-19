import os
import requests
import json
from modules.base_module import BaseModule

class GithubDorkingModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return []

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'github_dorks.json')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        auth_token = os.environ.get("GITHUB_TOKEN")
        if not auth_token:
            return {'results': [], 'count': 0, 'requests_made': 0}
            
        headers = {'Authorization': f'token {auth_token}', 'Accept': 'application/vnd.github.v3+json'}
        dorks = [f'"{target}" password', f'"{target}" secret', f'"{target}" api_key']
        
        results = []
        for dork in dorks:
            try:
                r = requests.get(f"https://api.github.com/search/code?q={dork}", headers=headers, timeout=10)
                items = r.json().get('items', [])
                results.extend(items)
            except:
                pass
                
        with open(host_out, 'w') as f:
            json.dump(results, f)
            
        return {'results': results, 'count': len(results), 'requests_made': len(dorks)}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('leaked_credentials', confidence='medium', source='github_dorking')
