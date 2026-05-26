import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("final_review_install", ROOT / "install.py")
install = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(install)


class InstallGstackTest(unittest.TestCase):
    def test_gstack_review_missing_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(install.has_gstack_review(Path(tmp)))

    def test_detects_prefixed_gstack_review_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / ".codex" / "skills" / "gstack-review" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: review\n---\n", encoding="utf-8")

            self.assertTrue(install.has_gstack_review(Path(tmp)))

    def test_detects_unprefixed_review_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / ".codex" / "skills" / "review" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: review\n---\n", encoding="utf-8")

            self.assertTrue(install.has_gstack_review(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
