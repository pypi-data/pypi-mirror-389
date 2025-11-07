"""API client for Gitizi"""

import requests
from typing import Dict, List, Optional, Any
from .config import config
from .constants import SUPABASE, LIMITS


class Prompt:
    """Prompt data model"""

    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.content = data.get("content", "")
        self.tags = data.get("tags", [])
        self.author = data.get("author", "")
        self.created_at = data.get("createdAt", data.get("created_at", ""))
        self.updated_at = data.get("updatedAt", data.get("updated_at", ""))


class SearchResult:
    """Search result data model"""

    def __init__(self, data: Dict[str, Any]):
        self.prompts = [Prompt(p) for p in data.get("prompts", [])]
        self.total = data.get("total", 0)


class GitiziAPI:
    """API client for interacting with Gitizi services"""

    def __init__(self):
        self.base_url = f"{SUPABASE.URL}/functions/v1"
        self.timeout = LIMITS.API_TIMEOUT

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with authentication"""
        user_token = token or config.get_token()
        auth_token = user_token or SUPABASE.ANON_KEY

        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    def _invoke_function(
        self, function_name: str, body: Optional[Dict[str, Any]] = None, token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke a Supabase Edge Function"""
        url = f"{self.base_url}/{function_name}"
        headers = self._get_headers(token)

        try:
            response = requests.post(
                url, json=body or {}, headers=headers, timeout=self.timeout
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status_code}: {response.reason}")
                except ValueError:
                    error_msg = f"HTTP {response.status_code}: {response.reason}"
                raise Exception(error_msg)

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def authenticate(self, token: str) -> Dict[str, Any]:
        """Authenticate with the API"""
        try:
            url = f"{self.base_url}/api-auth-verify"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                url, json={"token": token}, headers=headers, timeout=self.timeout
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status_code}: {response.reason}")
                except ValueError:
                    error_msg = f"HTTP {response.status_code}: {response.reason}"
                raise Exception(error_msg)

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication failed: {str(e)}")

    def search_prompts(self, query: str, limit: int = 10) -> SearchResult:
        """Search for prompts"""
        try:
            result = self._invoke_function("api-search-prompts", {"query": query, "limit": limit})
            return SearchResult(result)
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    def get_prompt(self, prompt_id: str) -> Prompt:
        """Get a single prompt by ID"""
        try:
            result = self._invoke_function("api-get-prompt", {"id": prompt_id})
            return Prompt(result)
        except Exception as e:
            raise Exception(f"Failed to fetch prompt: {str(e)}")

    def create_prompt(self, name: str, description: str, content: str, tags: List[str]) -> Prompt:
        """Create a new prompt"""
        try:
            data = {
                "name": name,
                "description": description,
                "content": content,
                "tags": tags,
            }
            result = self._invoke_function("api-create-prompt", data)
            return Prompt(result)
        except Exception as e:
            raise Exception(f"Failed to create prompt: {str(e)}")

    def update_prompt(
        self,
        prompt_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Prompt:
        """Update an existing prompt"""
        try:
            data = {"id": prompt_id}
            if name is not None:
                data["name"] = name
            if description is not None:
                data["description"] = description
            if content is not None:
                data["content"] = content
            if tags is not None:
                data["tags"] = tags

            result = self._invoke_function("api-update-prompt", data)
            return Prompt(result)
        except Exception as e:
            raise Exception(f"Failed to update prompt: {str(e)}")

    def list_user_prompts(self) -> List[Prompt]:
        """List all prompts for the authenticated user"""
        try:
            result = self._invoke_function("api-list-user-prompts")
            return [Prompt(p) for p in result]
        except Exception as e:
            raise Exception(f"Failed to list prompts: {str(e)}")

    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user info"""
        try:
            return self._invoke_function("api-get-current-user")
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")


# Global API instance
api = GitiziAPI()
