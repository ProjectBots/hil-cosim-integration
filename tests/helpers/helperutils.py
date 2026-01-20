import os

def clamp(value, min_value, max_value):
	"""Clamp a value between a minimum and maximum.
	
	Args:
		value (float): The value to clamp.
		min_value (float): The minimum value.
		max_value (float): The maximum value.
	
	Returns:
		float: The clamped value.
	"""
	return max(min_value, min(value, max_value))

def get_bool_env_var(var_name: str, default: bool = False) -> bool:
	"""Get a boolean environment variable.

	Args:
		var_name (str): The name of the environment variable.
		default (bool, optional): The default value if the variable is not set. Defaults to False.

	Returns:
		bool: The boolean value of the environment variable.
	"""
	val_str = os.getenv(var_name)
	if val_str is None:
		return default
	return val_str.lower() in ("1", "true", "yes", "on")