# Changelog - Bunnyshell Python SDK

All notable changes to this project will be documented in this file.

## [0.1.3] - 2025-10-28

### 🎯 Added
- **Template-based Sandbox Creation**: New `template_id` parameter in `Sandbox.create()` and `AsyncSandbox.create()`
  - Create sandboxes from templates without specifying resources (vcpu, memory, disk)
  - Resources are automatically loaded from the template
  - Simpler API for template-based workflows

### 🔄 Changed
- Made `template`, `vcpu`, and `memory_mb` parameters **optional** in `Sandbox.create()`
- Parameters are now conditionally validated based on creation mode:
  - **Template-based mode**: Only `template_id` required
  - **Custom mode**: `template`, `vcpu`, `memory_mb` required

### 📖 Usage Examples

#### Create from Template (NEW):
```python
from bunnyshell import Sandbox

# Simple: just specify template_id
sandbox = Sandbox.create(template_id="291")

# Resources (vcpu, memory, disk) loaded automatically from template
print(f"Sandbox: {sandbox.sandbox_id}")
print(f"URL: {sandbox.get_info().public_host}")
```

#### Create Custom Sandbox (UNCHANGED):
```python
# Old API still works - backwards compatible
sandbox = Sandbox.create(
    template="code-interpreter",
    vcpu=4,
    memory_mb=4096,
    disk_gb=20
)
```

### ✅ Backwards Compatibility
- **No breaking changes**
- Existing code continues to work without modifications
- Both sync (`Sandbox`) and async (`AsyncSandbox`) APIs updated

### 🧪 Testing
- ✅ End-to-end tests pass
- ✅ Template-based creation verified
- ✅ Backwards compatibility confirmed
- ✅ Production ready

### 📦 Installation
```bash
pip install --upgrade bunnyshell
```

### 🔗 Links
- PyPI: https://pypi.org/project/bunnyshell/0.1.3/
- Documentation: https://docs.bunnyshell.com
- GitHub: https://github.com/bunnyshell/bunnyshell-python

---

## [0.1.2] - Previous Release

### Features
- Template building with fluent API
- File upload support
- Build status monitoring
- SSH and SFTP access
- Desktop automation
- WebSocket terminal support
- Agent API integration

---

**Note:** Version 0.1.3 introduces template-based sandbox creation while maintaining full backwards compatibility.

