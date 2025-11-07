# json_mage.py - Your Personal JSON Grimoire (ULTIMATE EDITION)

import jmespath
from typing import Any, Union, List, Dict
import json
from collections import Counter


class MageJSON:
    """
    The simplest JSON sorcery - auto-converted to mage powers
    ULTIMATE EDITION with super simple counting & filtering!
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
    
    # === 🔥 SUPER SIMPLE COUNTING & FILTERING 🔥 ===
    
    def count(self, key: str, value: Any = None) -> Union[int, dict]:
        """
        Count occurrences - DEAD SIMPLE
        
        Examples:
            data.count('status', 'success')  # How many status='success'? → 3
            data.count('status')             # Count each status → {'success': 3, 'error': 2}
            data.count('name', 'John')       # How many name='John'? → 1
        """
        all_values = self.all(key)
        
        if value is None:
            # Return count of each unique value
            return dict(Counter(all_values))
        else:
            # Return count of specific value
            return all_values.count(value)
    
    def filter(self, key: str, value: Any) -> List:
        """
        Get ALL items where key=value
        
        Examples:
            data.filter('status', 'success')  # All successful items
            data.filter('age', 25)            # All items with age=25
            data.filter('name', 'John')       # All items with name='John'
        
        Returns list of matching items
        """
        # Handle strings vs numbers differently
        if isinstance(value, str):
            query = f"[?{key}=='{value}']"
        else:
            query = f"[?{key}==`{value}`]"
        
        result = self.where(query)
        return result if result else []
    
    def summary(self) -> dict:
        """
        Get COMPLETE summary of the data
        
        Examples:
            data.summary()  # Shows everything about your data
        
        Returns dict with all stats
        """
        result = {
            'type': 'list' if isinstance(self._raw, list) else 'dict',
            'total_items': len(self._raw) if isinstance(self._raw, list) else 1,
            'all_keys': self.keys,
            'key_counts': {}
        }
        
        # Count unique values for each key
        for key in self.keys:
            values = self.all(key)
            if values:
                result['key_counts'][key] = dict(Counter(values))
        
        return result
    
    def unique(self, key: str) -> List:
        """
        Get unique values for a key
        
        Examples:
            data.unique('status')  # ['success', 'error']
            data.unique('email')   # All unique emails
        """
        return list(set(self.all(key)))
    
    def has(self, key: str, value: Any) -> bool:
        """
        Check if ANY item has key=value
        
        Examples:
            data.has('status', 'error')  # True if any error exists
            data.has('name', 'John')     # True if John exists
        """
        return value in self.all(key)
    
    # === 🔥 MODIFICATION POWERS 🔥 ===
    
    def change(self, key: str, new_value: Any) -> 'MageJSON':
        """
        Change ANY key's value (finds it anywhere in the JSON)
        
        Examples:
            data.change('name', 'Farhan')
            data.change('status', 'success')
            data.change('email', 'new@email.com')
        
        Returns self for chaining
        """
        self._change_key(self._raw, key, new_value)
        return self
    
    def change_at(self, path: str, new_value: Any) -> 'MageJSON':
        """
        Change value at SPECIFIC path (dot notation)
        
        Examples:
            data.change_at('user.name', 'Farhan')
            data.change_at('data.metrics.requests', 200)
            data.change_at('status', 'success')
        
        Returns self for chaining
        """
        parts = path.split('.')
        current = self._raw
        
        # Navigate to the parent of the target
        for part in parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return self  # Path not found
        
        # Change the final key
        if isinstance(current, dict) and parts[-1] in current:
            current[parts[-1]] = new_value
        
        return self
    
    def add_key(self, key: str, value: Any) -> 'MageJSON':
        """
        Add a new key to the JSON (at root level if dict)
        
        Examples:
            data.add_key('new_field', 'new_value')
        
        Returns self for chaining
        """
        if isinstance(self._raw, dict):
            self._raw[key] = value
        return self
    
    def remove_key(self, key: str) -> 'MageJSON':
        """
        Remove a key from ANYWHERE in the JSON
        
        Examples:
            data.remove_key('password')
            data.remove_key('temp_data')
        
        Returns self for chaining
        """
        self._remove_key(self._raw, key)
        return self
    
    def save_to(self, filename: str) -> str:
        """
        Save the modified JSON to a file
        
        Examples:
            data.change('status', 'success').save_to('updated_data')
        
        Returns success message
        """
        try:
            import simple_file
            return simple_file.save(filename, self._raw)
        except:
            # Fallback if simple_file not available
            import json
            from pathlib import Path
            Path(filename).write_text(json.dumps(self._raw, indent=2))
            return f"✅ Saved: {filename}"
    
    # === DISPLAY ===
    
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
    
    def _change_key(self, data: Any, key: str, new_value: Any) -> bool:
        """Recursively change first occurrence of key"""
        if isinstance(data, dict):
            if key in data:
                data[key] = new_value
                return True
            for v in data.values():
                if self._change_key(v, key, new_value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._change_key(item, key, new_value):
                    return True
        return False
    
    def _remove_key(self, data: Any, key: str):
        """Recursively remove all occurrences of key"""
        if isinstance(data, dict):
            if key in data:
                del data[key]
            for v in list(data.values()):
                self._remove_key(v, key)
        elif isinstance(data, list):
            for item in data:
                self._remove_key(item, key)


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
