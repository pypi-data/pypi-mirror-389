# oci_chat_tracker/__init__.py

def apply_patch():
    """Apply the monkey patch for OCI client"""
    from .oci_chat_tracker import apply_patch as _apply_patch
    _apply_patch()
