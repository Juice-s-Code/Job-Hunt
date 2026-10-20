"""Synthetic, offline tests for the candidate-neutral starter CLI."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "jobhunt.py"


def example(**changes):
    job = dict(employer="Synthetic Example Employer", ats="example", id="EXAMPLE-01-A",
               title="Synthetic Finance Analyst", url="https://example.com/jobs/EXAMPLE-01-A",
               country="US", location="Synthetic City", role_family="finance",
               employment_type="full_time", internship=False, min_years_experience=0,
               start_date="2030-07-01",
               source_text="SYNTHETIC ONLY. Full-time finance analyst, 0 years, July 1 2030 start.",
               salary_min=75000, salary_currency="USD", salary_period="annual", no_ai=False)
    job.update(changes)
    return job


class CoreTests(unittest.TestCase):
    def setUp(self):
        # The test runner may choose its private cache as TMP/TEMP. Never use Starter.
        parent = Path(tempfile.gettempdir()).resolve()
        if parent == CLI.parent or CLI.parent in parent.parents:
            raise RuntimeError("Synthetic test temporary directories must be outside Starter")
        self.tmp = tempfile.TemporaryDirectory(prefix="synthetic-jobhunt-", dir=parent)
        self.root = Path(self.tmp.name).resolve()
        self.vault = self.root / "private-vault"
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    def tearDown(self):
        self.tmp.cleanup()

    def runcli(self, command, *args, ok=True):
        result = subprocess.run([sys.executable, "-B", str(CLI), command, "--vault",
                                 str(self.vault), *map(str, args)], cwd=self.root,
                                env=self.env, text=True, capture_output=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(result.stderr)
        return result

    def init(self, ready=True):
        self.runcli("init")
        if ready:
            path = self.vault / "Profile" / "candidate.json"
            profile = json.loads(path.read_text())
            profile["candidate"].update(display_name="Synthetic Person",
                                        email="synthetic@example.invalid", earliest_start="2030-06-01")
            profile["mandate"].update(role_families=["finance"], countries=["US"], salary_floor=70000)
            path.write_text(json.dumps(profile), encoding="utf-8")
        return self.vault

    def jobs(self, *jobs):
        path = self.root / "synthetic-jobs.json"
        path.write_text(json.dumps(list(jobs)), encoding="utf-8")
        result = self.runcli("import-jobs", "--file", path)
        return result["keys"]

    def screen(self):
        return {x["key"]: x for x in self.runcli("screen")["jobs"]}

    def tree(self):
        return {str(p.relative_to(self.vault)): p.read_bytes()
                for p in self.vault.rglob("*") if p.is_file()}

    def receipts(self):
        evidence = self.root / "synthetic-confirmation.txt"
        resume = self.root / "synthetic-resume.txt"
        evidence.write_text("SYNTHETIC ONLY: matching employer receipt and one inbox confirmation.")
        resume.write_text("SYNTHETIC ONLY: no actual candidate.")
        return evidence, resume

    def claim(self, key, owner="synthetic-operator"):
        return self.runcli("claim", "--key", key, "--owner", owner)

    def finish(self, key, owner="synthetic-operator", **changes):
        evidence, resume = self.receipts()
        args = ["--key", key, "--owner", owner, "--evidence", evidence, "--resume", resume,
                "--confirmation-count", str(changes.get("count", 1))]
        if changes.get("verified", True):
            args.append("--identity-verified")
        return self.runcli("receipt", *args, ok=changes.get("ok", True))

    def test_blank_init_privacy_and_doctor(self):
        self.init(False)
        p = json.loads((self.vault / "Profile/candidate.json").read_text())
        self.assertEqual(p["candidate"]["display_name"], "")
        self.assertIsNone(p["candidate"]["graduation_date"])
        self.assertEqual(p["mandate"]["countries"], [])
        self.assertIsNone(p["mandate"]["salary_floor"])
        for name in ["AGENTS.md", "CLAUDE.md", ".gitignore", "Cursor.MD/HERMES COORDINATION.md",
                     "Cursor.MD/SUBMIT LOCK.md", "Cursor.MD/STATE.md", "Cursor.MD/HANDOFF.md",
                     "Applications/Application Ledger.md", "Profile/Owner Answers.md"]:
            self.assertTrue((self.vault / name).is_file(), name)
        self.assertEqual(self.runcli("ledger")["applications"], 0)
        result = self.runcli("doctor", ok=False)
        self.assertNotIn("synthetic@", result.stdout + result.stderr)

    def test_ready_doctor_does_not_print_profile_values(self):
        self.init()
        result = self.runcli("doctor")
        self.assertTrue(result["ready"])
        self.assertNotIn("Synthetic Person", json.dumps(result))
        self.assertNotIn("synthetic@example", json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_init_existing_and_framework_refusal_unchanged(self):
        self.init()
        before = self.tree()
        self.runcli("init", ok=False)
        self.assertEqual(before, self.tree())
        result = subprocess.run([sys.executable, "-B", str(CLI), "init", "--vault", str(CLI.parent)],
                                capture_output=True, text=True, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        sentinel = self.root / "occupied"
        sentinel.mkdir()
        (sentinel / "keep").write_text("unchanged")
        result = subprocess.run([sys.executable, "-B", str(CLI), "init", "--vault", str(sentinel)],
                                capture_output=True, text=True, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(sentinel.iterdir()), [sentinel / "keep"])

    def test_import_transactionality_exact_ids_and_dedupe(self):
        self.init()
        first = self.jobs(example())[0]
        self.assertEqual(self.jobs(example()), [first])
        other = self.jobs(example(id="example-01-a"), example(employer="Other Synthetic Employer",
                          url="https://example.org/jobs/EXAMPLE-01-A"))[1]
        self.assertNotEqual(first, other)
        self.assertEqual(len(self.screen()), 3)
        before = self.tree()
        self.jobs_invalid([example(id="valid-new"), example(id=17)])
        self.assertEqual(before, self.tree())
        self.jobs_invalid([example(id="EXAMPLE-01-A", title="Conflicting title")])
        self.assertEqual(before, self.tree())

    def jobs_invalid(self, jobs):
        path = self.root / "invalid.json"
        path.write_text(json.dumps(jobs), encoding="utf-8")
        return self.runcli("import-jobs", "--file", path, ok=False)

    def test_strict_json_types_controls_and_unknown_fields(self):
        self.init()
        for change in [dict(no_ai="false"), dict(min_years_experience=True),
                       dict(start_date="20300701"), dict(salary_min=-1), dict(extra="unknown"),
                       dict(id="../bad"), dict(title="bad\x1btitle"), dict(title="bad\u0085title"),
                       dict(title="bad\u202etitle"), dict(url="file:///tmp/test")]:
            self.jobs_invalid([example(**change)])
        path = self.root / "invalid.json"
        for raw in ['[{"id":"one","id":"two"}]', '[NaN]', '{}']:
            path.write_text(raw)
            self.runcli("import-jobs", "--file", path, ok=False)
        self.assertEqual(len(self.screen()), 0)

    def test_screen_eligibility_unknowns_rejections_and_no_ai(self):
        self.init()
        changes = [{}, {"start_date": None}, {"source_text": ""}, {"employment_type": None},
                   {"min_years_experience": None}, {"country": None}, {"role_family": None},
                   {"salary_min": 69000}, {"salary_min": None, "salary_period": None},
                   {"salary_period": "hourly"}, {"salary_currency": "EUR"},
                   {"no_ai": True}, {"no_ai": None}, {"internship": True},
                   {"min_years_experience": 2}, {"start_date": "2030-01-01"},
                   {"title": "Senior Finance Manager"}, {"country": "CA"}]
        keys = self.jobs(*(example(id="SYNTHETIC-" + str(i), **c) for i, c in enumerate(changes)))
        rows = self.screen()
        expected = ["eligible", "review", "review", "review", "review", "review", "review",
                    "ineligible", "eligible", "review", "review", "OWNER_MANUAL", "review",
                    "ineligible", "ineligible", "ineligible", "review", "ineligible"]
        self.assertEqual([rows[k]["status"] for k in keys], expected)
        for i in range(1, len(keys)):
            if expected[i] != "eligible":
                self.runcli("claim", "--key", keys[i], "--owner", "synthetic", ok=False)

    def test_incomplete_and_invalid_mandate_never_claimable(self):
        self.init(False)
        key = self.jobs(example())[0]
        self.runcli("screen", ok=False)
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)
        path = self.vault / "Profile/candidate.json"
        p = json.loads(path.read_text())
        p["mandate"]["max_required_experience_years"] = True
        path.write_text(json.dumps(p))
        self.runcli("doctor", ok=False)

    def test_null_salary_requires_owner_record(self):
        self.init()
        path = self.vault / "Profile/candidate.json"
        p = json.loads(path.read_text()); p["mandate"]["salary_floor"] = None
        path.write_text(json.dumps(p))
        self.runcli("doctor", ok=False)
        (self.vault / "Profile/Owner Answers.md").write_text("SYNTHETIC OWNER: no salary floor.")
        self.assertTrue(self.runcli("doctor")["ready"])

    def test_global_claim_lock_owner_and_park_hold(self):
        self.init()
        a, b = self.jobs(example(), example(id="SYNTHETIC-SECOND", title="Different Analyst"))
        self.claim(a)
        self.runcli("claim", "--key", b, "--owner", "other", ok=False)
        self.runcli("claim", "--key", a, "--owner", "synthetic-operator", ok=False)
        self.runcli("park", "--key", a, "--owner", "other", "--reason", "Synthetic stop", ok=False)
        self.runcli("park", "--key", a, "--owner", "synthetic-operator", "--reason", "Synthetic hold", "--unsent")
        self.runcli("claim", "--key", a, "--owner", "synthetic-operator", ok=False)
        self.claim(b)

    def test_cross_process_claim_collision(self):
        self.init()
        key = self.jobs(example())[0]
        processes = [subprocess.Popen([sys.executable, "-B", str(CLI), "claim", "--vault",
                                       str(self.vault), "--key", key, "--owner", owner],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, env=self.env)
                     for owner in ["synthetic-a", "synthetic-b"]]
        results = [p.communicate(timeout=15) for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1], results)

    def test_stale_mutation_lock_never_auto_released(self):
        self.init()
        key = self.jobs(example())[0]
        lock = self.vault / ".jobhunt/mutation.lock"
        lock.write_text("synthetic outstanding lock")
        os.utime(lock, (1, 1))
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)
        self.assertEqual(lock.read_text(), "synthetic outstanding lock")

    def test_receipt_prerequisites_and_hashes_ledger(self):
        self.init()
        key = self.jobs(example())[0]
        self.finish(key, ok=False)
        self.claim(key)
        for args in [dict(count=0), dict(count=2), dict(verified=False), dict(owner="other")]:
            self.finish(key, ok=False, **args)
        evidence, resume = self.receipts()
        result = self.finish(key)
        self.assertEqual(self.runcli("ledger")["applications"], 1)
        receipt = json.loads((self.vault / "Receipts" / (key + ".json")).read_text())
        self.assertEqual(receipt["evidence_sha256"], hashlib.sha256(evidence.read_bytes()).hexdigest())
        self.assertEqual(receipt["resume_sha256"], hashlib.sha256(resume.read_bytes()).hexdigest())
        self.finish(key, ok=False)
        self.runcli("claim", "--key", key, "--owner", "synthetic-operator", ok=False)

    def test_empty_receipt_and_unknown_key_refused(self):
        self.init()
        key = self.jobs(example())[0]; self.claim(key)
        evidence, resume = self.receipts(); evidence.write_text("")
        self.runcli("receipt", "--key", key, "--owner", "synthetic-operator",
                    "--evidence", evidence, "--resume", resume, "--confirmation-count", 1,
                    "--identity-verified", ok=False)
        self.runcli("park", "--key", "missing", "--owner", "synthetic",
                    "--reason", "Synthetic", ok=False)
        self.assertEqual(self.runcli("ledger")["applications"], 0)

    def test_ledger_and_receipt_tampering_fail_loudly(self):
        self.init()
        key = self.jobs(example())[0]; self.claim(key); self.finish(key)
        ledger = self.vault / "Applications/Application Ledger.md"
        old = ledger.read_bytes(); ledger.write_text("# invented application\n")
        self.runcli("ledger", ok=False)
        self.runcli("import-jobs", "--file", self.root / "synthetic-jobs.json", ok=False)
        ledger.write_bytes(old)
        receipt = self.vault / "Receipts" / (key + ".json")
        p = json.loads(receipt.read_text()); p["resume_sha256"] = "0" * 64
        receipt.write_text(json.dumps(p))
        self.runcli("ledger", ok=False)

    def test_same_employer_role_variant_held_after_claim(self):
        self.init()
        a, b = self.jobs(example(), example(id="VARIANT", location="Other Synthetic City"))
        self.claim(a)
        self.runcli("park", "--key", a, "--owner", "synthetic-operator", "--reason", "Synthetic unsent hold", "--unsent")
        self.runcli("claim", "--key", b, "--owner", "synthetic-operator", ok=False)

    def test_receipt_write_precedes_applied_and_failure_preserves_hold(self):
        self.init()
        key = self.jobs(example())[0]; self.claim(key)
        spec = importlib.util.spec_from_file_location("synthetic_jobhunt_core", CLI)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        original = module.atomic_write
        observed = []
        def intercept(path, content):
            if Path(path).name == "Application Ledger.md":
                observed.append((self.vault / "Receipts" / (key + ".json")).is_file())
                raise OSError("synthetic disk failure")
            return original(path, content)
        module.atomic_write = intercept
        evidence, resume = self.receipts()
        code = module.main(["receipt", "--vault", str(self.vault), "--key", key,
                            "--owner", "synthetic-operator", "--evidence", str(evidence),
                            "--resume", str(resume), "--confirmation-count", "1",
                            "--identity-verified"])
        self.assertNotEqual(code, 0)
        self.assertEqual(observed, [True])
        self.runcli("claim", "--key", key, "--owner", "other", ok=False)
        self.runcli("ledger", ok=False)

    def test_help_and_no_submit_command(self):
        result = subprocess.run([sys.executable, "-B", str(CLI), "--help"],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0)
        for cmd in ["init", "doctor", "import-jobs", "review-job", "screen", "claim", "park", "receipt", "ledger"]:
            result = subprocess.run([sys.executable, "-B", str(CLI), cmd, "--help"],
                                    capture_output=True, text=True, env=self.env)
            self.assertEqual(result.returncode, 0)
        self.runcli("submit", ok=False)

    def test_symlink_destination_and_symlink_input_refused(self):
        target = self.root / "synthetic-target"
        target.mkdir()
        marker = target / "keep"
        marker.write_text("SYNTHETIC UNCHANGED")
        link = self.root / "synthetic-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, "Synthetic junction setup failed")
        original = self.vault
        self.vault = link
        self.runcli("init", ok=False)
        self.assertEqual(marker.read_text(), "SYNTHETIC UNCHANGED")
        self.assertEqual(list(target.iterdir()), [marker])
        self.vault = original
        self.init()
        jobfile = target / "jobs.json"
        jobfile.write_text(json.dumps([example()]))
        self.runcli("import-jobs", "--file", link / "jobs.json", ok=False)

    def test_null_pay_does_not_hide_foreign_or_hourly_metadata(self):
        self.init()
        keys = self.jobs(example(salary_min=None, salary_currency="EUR", salary_period=None),
                         example(id="HOURLY", salary_min=None, salary_period="hourly"))
        self.assertEqual([self.screen()[k]["status"] for k in keys], ["review", "review"])

    def test_orphan_receipt_evidence_requires_reconciliation(self):
        self.init()
        key = self.jobs(example())[0]
        (self.vault / "Receipts" / (key + ".evidence")).write_text("SYNTHETIC interrupted write")
        self.runcli("ledger", ok=False)
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)



    def review(self, key, job, ok=True):
        path = self.root / "synthetic-review.json"
        path.write_text(json.dumps(job), encoding="utf-8")
        return self.runcli("review-job", "--key", key, "--file", path, ok=ok)

    def test_review_unknown_connector_job_end_to_end_with_title_padding(self):
        self.init()
        raw = example(title="Synthetic upstream analyst  ", country=None, role_family=None,
                      employment_type=None, internship=None, min_years_experience=None,
                      start_date=None, no_ai=None, salary_min=None, salary_period=None)
        key = self.jobs(raw)[0]
        self.assertEqual(self.screen()[key]["status"], "review")
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)
        enriched = example(title=raw["title"])
        self.review(key, enriched)
        self.assertEqual(self.screen()[key]["status"], "eligible")
        state = json.loads((self.vault / ".jobhunt/state.json").read_text())
        history = state["jobs"][key]["history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job"], raw)
        self.assertEqual(state["jobs"][key]["job"]["title"], raw["title"])
        before = self.tree()
        self.jobs_invalid([raw])  # Import never silently restores an old version.
        self.assertEqual(before, self.tree())
        self.claim(key)

    def test_review_identity_and_invalid_input_transactionality(self):
        self.init()
        original = example(no_ai=None)
        key = self.jobs(original)[0]
        for field, value in [("employer", "Other"), ("ats", "other"), ("id", "OTHER"),
                             ("title", "Renamed"), ("url", "https://example.com/other"),
                             ("no_ai", "false"), ("title", "bad\tname")]:
            before = self.tree()
            self.review(key, dict(original, **{field: value}), ok=False)
            self.assertEqual(before, self.tree())
        path = self.root / "synthetic-review.json"
        path.write_text('{"id":"one","id":"two"}')
        self.runcli("review-job", "--key", key, "--file", path, ok=False)
        self.review("missing", example(), ok=False)
        self.review(key, [example()], ok=False)

    def test_review_audit_chain_and_no_ai_cannot_be_cleared(self):
        self.init()
        raw = example(no_ai=None); key = self.jobs(raw)[0]
        blocked = example(no_ai=True)
        self.review(key, blocked)
        before = self.tree()
        for value in [False, None]:
            self.review(key, example(no_ai=value), ok=False)
            self.assertEqual(before, self.tree())
        changed = dict(blocked, source_text="SYNTHETIC verified employer AI prohibition.")
        self.review(key, changed)
        state = json.loads((self.vault / ".jobhunt/state.json").read_text())
        self.assertEqual([v["job"] for v in state["jobs"][key]["history"]], [raw, blocked])
        self.assertEqual(self.screen()[key]["status"], "OWNER_MANUAL")
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)
        state["jobs"][key]["history"][0]["job"]["id"] = "CORRUPTED"
        (self.vault / ".jobhunt/state.json").write_text(json.dumps(state))
        self.runcli("ledger", ok=False)

    def test_review_refuses_claimed_parked_applied_and_mutation_lock(self):
        self.init()
        a, b = self.jobs(example(), example(id="SECOND", title="Synthetic second analyst",
                                           url="https://example.com/second"))
        lock = self.vault / ".jobhunt/mutation.lock"
        lock.write_text("Synthetic outstanding lock")
        self.review(a, example(), ok=False); lock.unlink()
        self.claim(a)
        self.review(a, example(), ok=False)
        self.runcli("park", "--key", a, "--owner", "synthetic-operator",
                    "--reason", "Synthetic clean cessation", "--unsent")
        self.review(a, example(), ok=False)
        self.claim(b); self.finish(b)
        self.review(b, example(id="SECOND", title="Synthetic second analyst",
                              url="https://example.com/second"), ok=False)

    def test_no_ai_null_alone_stays_review(self):
        self.init()
        key = self.jobs(example(no_ai=None))[0]
        self.assertEqual(self.screen()[key]["status"], "review")
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)

    def test_title_padding_preserved_but_ids_not_repaired(self):
        self.init()
        key = self.jobs(example(title=" Synthetic title  "))[0]
        state = json.loads((self.vault / ".jobhunt/state.json").read_text())
        self.assertEqual(state["jobs"][key]["job"]["title"], " Synthetic title  ")
        self.jobs_invalid([example(id=" EXAMPLE-01-A ")])
        self.jobs_invalid([example(title="bad\nname")])

    def test_init_refuses_instruction_and_git_ancestors_before_writes(self):
        for marker in [".git", "CLAUDE.md", "AGENTS.md"]:
            parent = self.root / ("synthetic-parent-" + marker.replace(".", ""))
            parent.mkdir()
            (parent / marker).write_text("SYNTHETIC OTHER OWNER")
            self.vault = parent / "nested" / "new-vault"
            self.runcli("init", ok=False)
            self.assertFalse((parent / "nested").exists())
            self.assertEqual((parent / marker).read_text(), "SYNTHETIC OTHER OWNER")

    def test_display_rename_cannot_duplicate_same_exact_target(self):
        self.init()
        original = example()
        renamed = example(employer="SYNTHETIC EXAMPLE EMPLOYER",
                          title="Synthetic Analyst - Other Display")
        before = self.tree()
        self.jobs_invalid([original, renamed])
        self.assertEqual(before, self.tree())
        key = self.jobs(original)[0]
        self.jobs_invalid([renamed])
        self.claim(key); self.finish(key)
        self.jobs_invalid([renamed])
        self.assertEqual(self.runcli("ledger")["applications"], 1)

    def test_multiline_degree_guard(self):
        self.init()
        keys = self.jobs(example(source_text="SYNTHETIC Required:\nMaster's degree."),
                         example(id="PHD", source_text="SYNTHETIC PhD\nrequired."))
        for key in keys:
            self.assertEqual(self.screen()[key]["status"], "review")
            self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)

    def test_replaced_mutation_lock_is_not_deleted_by_prior_owner(self):
        self.init()
        spec = importlib.util.spec_from_file_location("synthetic_lock_core", CLI)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        lock = self.vault / ".jobhunt/mutation.lock"
        first = module.mutation_lock(self.vault); first.__enter__()
        lock.unlink()  # Synthetic reproduction of unsafe overlapping manual recovery.
        second = module.mutation_lock(self.vault); second.__enter__()
        try:
            expected = lock.read_bytes()
            first.__exit__(None, None, None)
            self.assertTrue(lock.exists())
            self.assertEqual(lock.read_bytes(), expected)
            with self.assertRaises(module.Problem):
                with module.mutation_lock(self.vault):
                    self.fail("A third owner acquired the second owner's lock")
        finally:
            second.__exit__(None, None, None)

    def test_ambiguous_submit_cannot_park_without_unsent_attestation(self):
        self.init()
        key = self.jobs(example())[0]; self.claim(key)
        before = self.tree()
        self.runcli("park", "--key", key, "--owner", "synthetic-operator",
                    "--reason", "Synthetic ambiguous submit, no confirmation", ok=False)
        self.assertEqual(before, self.tree())
        self.assertEqual(self.runcli("ledger")["active_claims"], 1)

    def test_actual_source_normalizer_to_reviewed_cli_without_network(self):
        self.init()
        spec = importlib.util.spec_from_file_location("synthetic_source_reader", CLI.parent / "source_jobs.py")
        source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
        fixture = {"jobs": [{"id": 123, "title": "Synthetic source analyst  ",
                             "absolute_url": "https://example.com/jobs/123",
                             "location": {"name": "Synthetic City"},
                             "content": "<p>SYNTHETIC public employer source only.</p>"}]}
        jobs = source.normalize(fixture, "Synthetic Example Employer")
        key = self.jobs(*jobs)[0]
        self.assertEqual(self.screen()[key]["status"], "review")
        self.runcli("claim", "--key", key, "--owner", "synthetic", ok=False)
        enriched = example(**{k: jobs[0][k] for k in ["employer", "ats", "id", "title", "url"]})
        self.review(key, enriched)
        self.assertEqual(self.screen()[key]["status"], "eligible")
        self.claim(key)


if __name__ == "__main__":
    unittest.main()
