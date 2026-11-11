import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BootPackagingTests(unittest.TestCase):
    def test_udev_service_payload_and_lifecycle(self):
        spec = (ROOT / "SPECS/udev.spec").read_text()
        service = re.search(
            r"cat > %\{buildroot\}/etc/init\.d/udev << 'EOF'\n(.*?)\nEOF",
            spec,
            re.DOTALL,
        )
        self.assertIsNotNone(service, "udev must ship an OpenRC service")
        source = service.group(1)
        self.assertIn("need dev-mount sysfs", source)
        self.assertIn("before network dhcpcd", source)
        self.assertIn("provide dev", source)
        self.assertIn(
            "ln -sv ../../init.d/udev %{buildroot}/etc/runlevels/sysinit/udev", spec
        )
        self.assertIn("chmod 755 %{buildroot}/etc/init.d/udev", spec)
        self.assertIn("%files -f %{_builddir}/udev-files.list", spec)
        self.assertIn("find . -type f -o -type l", spec)
        self.assertRegex(spec, r"(?m)^Requires:\s+openrc$")
        expected = [
            "udevd:--daemon",
            "udevadm:trigger --action=add --type=subsystems",
            "udevadm:trigger --action=add --type=devices",
            "udevadm:settle --timeout=30",
        ]
        with tempfile.TemporaryDirectory(prefix="maqui-boot-test-") as directory:
            root = Path(directory)
            service_path = root / "udev"
            service_path.write_text(source)
            subprocess.run(["/bin/sh", "-n", str(service_path)], check=True)
            for name in ["udevd", "udevadm"]:
                path = root / name
                path.write_text(
                    "#!/bin/sh\n"
                    f"printf '%s\\n' '{name}:'\"$*\" >> \"$TRACE_PATH\"\n"
                    f"[ \"$FAIL_ACTION\" != '{name}:'\"$*\" ]\n"
                )
                path.chmod(0o755)
            trace = root / "trace"
            for failure in [""] + expected:
                with self.subTest(failure=failure):
                    trace.write_text("")
                    environment = dict(
                        os.environ,
                        PATH=f"{root}:{os.environ.get('PATH', '')}",
                        TRACE_PATH=str(trace),
                        FAIL_ACTION=failure,
                    )
                    result = subprocess.run(
                        [
                            "/bin/sh", "-c",
                            'ebegin() { :; }; eend() { return "$1"; }; '
                            '. "$1"; command="$2"; start',
                            "probe", str(service_path), str(root / "udevd"),
                        ],
                        env=environment, capture_output=True, text=True,
                    )
                    actions = trace.read_text().splitlines()
                    if not failure:
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(actions, expected)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        prefix = expected[:expected.index(failure) + 1]
                        if failure != expected[0]:
                            prefix += ["udevadm:control --exit"]
                        self.assertEqual(actions, prefix)
            for failure in ["", "udevadm:control --exit"]:
                trace.write_text("")
                result = subprocess.run(
                    [
                        "/bin/sh", "-c",
                        'ebegin() { :; }; eend() { return "$1"; }; . "$1"; stop',
                        "probe", str(service_path),
                    ],
                    env=dict(environment, FAIL_ACTION=failure),
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 1 if failure else 0)
                self.assertEqual(trace.read_text().splitlines(), ["udevadm:control --exit"])

    def test_ca_package_owns_default_link_and_preserves_existing_paths(self):
        ca = (ROOT / "SPECS/ca-certificates.spec").read_text()
        release = (ROOT / "SPECS/maquilinux-release.spec").read_text()
        self.assertIn(
            "ln -sv certs/ca-certificates.crt %{buildroot}/etc/ssl/cert.pem", ca
        )
        self.assertIn("/etc/ssl/cert.pem", ca.split("%files", 1)[1])
        for path in [
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/pki/tls/certs/ca-bundle.trust.crt",
        ]:
            self.assertIn(path, ca.split("%files", 1)[1])
        self.assertRegex(release, r"(?m)^Requires:\s+ca-certificates$")
        self.assertRegex(release, r"(?m)^Requires:\s+dhcpcd$")
        self.assertRegex(release, r"(?m)^Requires:\s+udev$")
        self.assertIn("rc-update add dhcpcd default", release)
        self.assertIn("cacert = /etc/ssl/certs/ca-certificates.crt", release)
        self.assertNotRegex(release, r"ln\s+-s[fv]*.*\s/etc/ssl/cert\.pem")


if __name__ == "__main__":
    unittest.main()
