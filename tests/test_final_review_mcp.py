from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "final_review_mcp.py"


def load_module():
    spec = importlib.util.spec_from_file_location("final_review_mcp", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FinalReviewMcpTest(unittest.TestCase):
    def test_untracked_symlink_is_not_read(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.NamedTemporaryFile("w") as secret:
            root = Path(repo_dir)
            secret.write("outside-secret\n")
            secret.flush()
            (root / "innocuous.txt").symlink_to(secret.name)

            result = module._read_small_text(root, "innocuous.txt")

        self.assertFalse(result["included"])
        self.assertEqual(result["reason"], "symlink not included")

    def test_pr_command_failure_sets_top_level_error(self):
        module = load_module()
        packet = module._merge_command_status(
            {
                "scope": "pr",
                "view": {"ok": False, "stderr": "view failed"},
                "diff": {"ok": True, "stderr": ""},
            }
        )

        self.assertIn("error", packet)
        self.assertIn("view failed", packet["error"])

    def test_gitlab_mr_url_is_resolved_to_iid_and_repo(self):
        module = load_module()

        iid, repo = module._parse_gitlab_mr_identifier(
            "https://gitlab.example.com/group/sub/project/-/merge_requests/123"
        )

        self.assertEqual(iid, "123")
        self.assertEqual(repo, "https://gitlab.example.com/group/sub/project")

    def test_gitlab_plain_mr_identifier_is_unchanged(self):
        module = load_module()

        iid, repo = module._parse_gitlab_mr_identifier("feature-branch")

        self.assertEqual(iid, "feature-branch")
        self.assertIsNone(repo)

    def test_gitlab_mr_url_is_passed_to_glab_with_repo_flag(self):
        module = load_module()
        commands = []
        original_which = module.which
        original_run = module._run

        def fake_which(name):
            return "/usr/bin/glab" if name == "glab" else original_which(name)

        def fake_run(args, root, timeout=30):
            commands.append(args)
            return {"ok": True, "cmd": args, "returncode": 0, "stdout": "", "stderr": ""}

        try:
            module.which = fake_which
            module._run = fake_run

            packet = module._collect_mr(
                Path("/tmp"),
                "https://gitlab.example.com/group/sub/project/-/merge_requests/123",
            )
        finally:
            module.which = original_which
            module._run = original_run

        self.assertNotIn("error", packet)
        self.assertEqual(packet["resolved_identifier"], "123")
        self.assertEqual(packet["repo"], "https://gitlab.example.com/group/sub/project")
        self.assertIn(["glab", "mr", "view", "123", "-R", "https://gitlab.example.com/group/sub/project"], commands)
        self.assertIn(["glab", "mr", "diff", "123", "-R", "https://gitlab.example.com/group/sub/project"], commands)


if __name__ == "__main__":
    unittest.main()
