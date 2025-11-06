# json_mage.py - Your Personal JSON Grimoire

import jmespath
from typing import Any, Union, List, Dict
import json


class MageJSON:
    """
    The simplest JSON sorcery - auto-converted to mage powers
    """
    
    def __init__(self, data: Union[str, dict, list]):
        """Auto-converts anything to workable JSON"""
        if isinstance(data, str):
            try:
                self._raw = json.loads(data)
            except:
                self._raw = data
        else:
            self._raw = data
    
    # === YOUR SIMPLE COMMANDS ===
    
    @property
    def first(self) -> Any:
        """Get first item - mage.first"""
        if isinstance(self._raw, list):
            return self._raw[0] if self._raw else None
        elif isinstance(self._raw, dict):
            return list(self._raw.values())[0] if self._raw else None
        return self._raw
    
    @property
    def last(self) -> Any:
        """Get last item - mage.last"""
        if isinstance(self._raw, list):
            return self._raw[-1] if self._raw else None
        elif isinstance(self._raw, dict):
            return list(self._raw.values())[-1] if self._raw else None
        return self._raw
    
    @property
    def keys(self) -> List[str]:
        """All unique keys - mage.keys"""
        keys = set()
        self._collect_keys(self._raw, keys)
        return sorted(list(keys))
    
    @property
    def raw(self) -> Any:
        """Get raw data - mage.raw"""
        return self._raw
    
    def get(self, key: str) -> Any:
        """
        Get any key from anywhere - mage.get('key')
        Works with dot notation: mage.get('user.email')
        """
        # Try JMESPath first (handles dot notation)
        result = jmespath.search(key, self._raw)
        if result is not None:
            return result
        
        # Deep search if not found
        return self._deep_search(self._raw, key)
    
    def find(self, value: Any) -> List:
        """
        Find all items with this value - mage.find('john@email.com')
        Returns list of parent objects containing the value
        """
        return self._find_value(self._raw, value)
    
    def all(self, key: str) -> List:
        """
        Get ALL occurrences of a key - mage.all('email')
        Searches entire JSON structure
        """
        return self._collect_all_values(self._raw, key)
    
    def where(self, jmes_query: str) -> Any:
        """
        Custom JMESPath query - mage.where("users[?age > `25`].name")
        For when you need raw power
        """
        return jmespath.search(jmes_query, self._raw)
    
    @property
    def show(self) -> str:
        """Pretty print - print(mage.show)"""
        return json.dumps(self._raw, indent=2)
    
    def __repr__(self):
        """When you just print(mage)"""
        return self.show
    
    def __getitem__(self, key):
        """Direct access - mage['users'] or mage[0]"""
        if isinstance(self._raw, (dict, list)):
            return self._raw[key]
        return None
    
    # === INTERNAL MAGIC ===
    
    def _deep_search(self, data: Any, key: str) -> Any:
        """Recursively find key"""
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for v in data.values():
                result = self._deep_search(v, key)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._deep_search(item, key)
                if result is not None:
                    return result
        return None
    
    def _find_value(self, data: Any, target_value: Any) -> List:
        """Find objects containing value"""
        matches = []
        
        if isinstance(data, dict):
            if target_value in data.values():
                matches.append(data)
            for v in data.values():
                matches.extend(self._find_value(v, target_value))
        elif isinstance(data, list):
            for item in data:
                if item == target_value:
                    matches.append(item)
                else:
                    matches.extend(self._find_value(item, target_value))
        
        return matches
    
    def _collect_keys(self, data: Any, keys: set):
        """Collect all keys"""
        if isinstance(data, dict):
            keys.update(data.keys())
            for v in data.values():
                self._collect_keys(v, keys)
        elif isinstance(data, list):
            for item in data:
                self._collect_keys(item, keys)
    
    def _collect_all_values(self, data: Any, key: str) -> List:
        """Collect all values for key"""
        values = []
        
        if isinstance(data, dict):
            if key in data:
                values.append(data[key])
            for v in data.values():
                values.extend(self._collect_all_values(v, key))
        elif isinstance(data, list):
            for item in data:
                values.extend(self._collect_all_values(item, key))
        
        return values


# === THE MAGIC SPELL ===
def modify(data: Union[str, dict, list]) -> MageJSON:
    """
    Cast the spell - modify(response)
    Converts ANY JSON into your mage object
    """
    return MageJSON(data)


# For those who want the old way too
def myjson(data: Union[str, dict, list]) -> MageJSON:
    """Alternative name - same magic"""
    return MageJSON(data)


# Export both
__all__ = ['modify', 'myjson']
