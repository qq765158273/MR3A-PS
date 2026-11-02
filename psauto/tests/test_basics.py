import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from psauto.config import load_config
from psauto.imaging import png_to_bgr
from psauto.keymap import vk_to_key


class ConfigTests(unittest.TestCase):
    def test_loads_config_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"jumpserver_url": "https://example.invalid"}), encoding="utf-8")
            config = load_config(path)
            self.assertEqual(config.resolve_path(config.storage_state), path.parent / "state/storage.json")
        self.assertEqual(config.jumpserver_url, "https://example.invalid")
        self.assertEqual(config.viewport_width, 1600)
        self.assertTrue(config.headless)


class ImageTests(unittest.TestCase):
    def test_converts_rgb_and_rgba_to_contiguous_bgr(self):
        for mode, color, expected in [
            ("RGB", (255, 0, 0), [0, 0, 255]),
            ("RGBA", (0, 255, 0, 128), [0, 255, 0]),
        ]:
            with self.subTest(mode=mode):
                output = io.BytesIO()
                Image.new(mode, (4, 2), color).save(output, format="PNG")
                result = png_to_bgr(output.getvalue())
                self.assertEqual(result.shape, (2, 4, 3))
                self.assertEqual(result.dtype, np.uint8)
                self.assertTrue(result.flags.c_contiguous)
                self.assertEqual(result[0, 0].tolist(), expected)


class KeymapTests(unittest.TestCase):
    def test_common_win32_keys(self):
        for code, expected in [(13, "Enter"), (27, "Escape"), (0x41, "a"), (0x30, "0"), (0x74, "F5")]:
            with self.subTest(code=code):
                self.assertEqual(vk_to_key(code), expected)

    def test_unknown_key_is_rejected(self):
        with self.assertRaises(KeyError):
            vk_to_key(0xFF)


if __name__ == "__main__":
    unittest.main()
