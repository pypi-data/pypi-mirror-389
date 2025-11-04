import subprocess
import json
import requests
from typing import Optional, List
from .retriever import SearchResult

class LLMAgent:
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('llm.enabled', False)
        self.model = config.get('llm.model', 'llama3')
        self.max_tokens = config.get('llm.max_tokens', 500)
        self.temperature = config.get('llm.temperature', 0.1)
        self.use_api = config.get('llm.use_api', True)  # Prefer API over CLI
        self.api_timeout = config.get('llm.timeout', 120)  # 2 minutes default
    
    def explain_results(self, query: str, results: List[SearchResult]) -> Optional[str]:
        """Generate explanation for search results using LLM."""
        if not self.enabled:
            return None
        
        if not self._check_ollama():
            print("Warning: Ollama not available, skipping LLM explanation")
            return None
        
        context = self._prepare_context(results)
        prompt = self._create_explanation_prompt(query, context)
        
        try:
            return self._query_ollama(prompt)
        except Exception as e:
            print(f"Warning: LLM query failed: {e}")
            return None
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        if self.use_api:
            # Check API endpoint
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                return response.status_code == 200
            except:
                return False
        else:
            # Check CLI
            try:
                result = subprocess.run(['ollama', 'list'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
    
    def _prepare_context(self, results: List[SearchResult]) -> str:
        """Prepare context from search results with smart truncation."""
        context_parts = []
        max_context_lines = self.config.get('llm.max_context_lines', 100)
        
        for i, result in enumerate(results[:3]):  
            chunk = result.chunk
            content = chunk.content
            
            lines = content.split('\n')
            if len(lines) > max_context_lines:
                content = '\n'.join(lines[:max_context_lines])
                content += f"\n... (truncated, {len(lines) - max_context_lines} more lines)"
            
            context_parts.append(f"""
--- File: {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}) ---
{content}
""")
        
        return '\n'.join(context_parts)
    
    def _create_explanation_prompt(self, query: str, context: str) -> str:
        """Create prompt for LLM explanation."""
        return f"""You are a code analysis assistant. A user asked: "{query}"

Here are the relevant code segments I found:

{context}

Please provide a clear, concise explanation that answers the user's question based on the code above. 
Focus on:
1. Directly answering their question
2. Explaining what the relevant code does
3. Highlighting key parts that relate to their query

Keep your response under {self.max_tokens} words and be specific to the code shown.

Answer:"""
    
    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama with the given prompt."""
        if self.use_api:
            return self._query_ollama_api(prompt)
        else:
            return self._query_ollama_cli(prompt)
    
    def _query_ollama_api(self, prompt: str) -> str:
        """Query Ollama via HTTP API (more reliable than CLI)."""
        try:
            print("Querying Ollama API...")
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,  
                    'options': {
                        'temperature': self.temperature,
                        'num_predict': self.max_tokens
                    }
                },
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
                
        except requests.Timeout:
            raise Exception(f"Ollama API timed out after {self.api_timeout}s")
        except requests.ConnectionError:
            raise Exception("Cannot connect to Ollama API at localhost:11434")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _query_ollama_cli(self, prompt: str) -> str:
        """Query Ollama via CLI (fallback method)."""
        cmd = ['ollama', 'run', self.model]
        
        try:
            print("Querying Ollama CLI...")
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=prompt, timeout=self.api_timeout)
            
            if process.returncode != 0:
                raise Exception(f"Ollama CLI error: {stderr}")
            
            return stdout.strip()
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception(f"Ollama CLI timed out after {self.api_timeout}s")
        except FileNotFoundError:
            raise Exception("Ollama CLI not found. Is Ollama installed?")