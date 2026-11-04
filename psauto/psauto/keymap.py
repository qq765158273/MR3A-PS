"""Translate Win32 virtual-key codes to Playwright key names."""

_NAMED = {
    0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift",
    0x11: "Control", 0x12: "Alt", 0x1B: "Escape", 0x20: " ",
    0x21: "PageUp", 0x22: "PageDown", 0x23: "End", 0x24: "Home",
    0x25: "ArrowLeft", 0x26: "ArrowUp", 0x27: "ArrowRight", 0x28: "ArrowDown",
    0x2D: "Insert", 0x2E: "Delete",
}


def vk_to_key(vk: int) -> str:
    # Windows Forms Keys modifier flags keep a chord in one Maa ClickKey integer.
    # This mapping belongs to the input adapter; the pipeline still owns the action.
    if vk > 0xFFFF:
        if vk & ~0x700FF:
            raise KeyError(vk)
        modifiers = [name for flag, name in [(0x20000, 'Control'), (0x40000, 'Alt'), (0x10000, 'Shift')]
                     if vk & flag]
        return '+'.join([*modifiers, vk_to_key(vk & 0xFF)])
    if vk in _NAMED:
        return _NAMED[vk]
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x41 <= vk <= 0x5A:
        return chr(vk).lower()
    if 0x70 <= vk <= 0x7B:
        return f"F{vk - 0x6F}"
    raise KeyError(vk)
