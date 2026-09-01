import unittest

import server_algorithme as app


class InputValidationTests(unittest.TestCase):
    def test_username_accepts_safe_values(self):
        self.assertEqual(app.sanitize_username("alice_01"), "alice_01")
        self.assertEqual(app.sanitize_username("  alice  "), "alice")

    def test_username_rejects_injection_like_values(self):
        for bad in ["", "john doe", "admin'; DROP TABLE users; --", "a" * 65, "admin\x00test"]:
            self.assertIsNone(app.sanitize_username(bad))

    def test_tag_rejects_bad_values(self):
        self.assertIsNone(app.sanitize_tag_name("tag;DROP TABLE users;--"))
        self.assertIsNone(app.sanitize_tag_name(""))
        self.assertEqual(app.sanitize_tag_name("  nature-cinema  "), "nature-cinema")

    def test_comment_is_truncated_and_stripped(self):
        self.assertEqual(app.sanitize_comment_text("  bonjour  "), "bonjour")
        self.assertEqual(len(app.sanitize_comment_text("x" * 2000)), 1000)


if __name__ == "__main__":
    unittest.main()
