import config # For DEFAULT_ENCODING

# --- Data Display Utilities ---

def safe_display(value_to_display: any) -> str:
    """
    Safely converts a value to a string for display, handling None and bytes.
    """
    if value_to_display is None:
        return "N/A" # Or "None", "", depending on desired display for None values
    if isinstance(value_to_display, bytes):
        # Attempt to decode bytes to string, replacing invalid characters
        return value_to_display.decode(config.DEFAULT_ENCODING, 'replace')
    return str(value_to_display)