import hashlib
from pathlib import Path
EXPECTED = {'payload.part0a0': '953b39d06ef2dbdd093b942021ed89f54cc4d0f4da3bcd2c2db4407d1934d72b', 'payload.part0a1': 'bfa2b7990755aac3fca730f1e0499217cf25ae5a4d8c3a2881be709ca89eaf79', 'payload.part0a2': '1e03e1738c323890aabaf43c9f82e25b59af6f9a8ef1a6ac9cc14c7d5419d008', 'payload.part0a3': '47f171275a865dbbdb45bf9f9922eee209f3e6a158daec5e3e0bfb2b02f713c', 'payload.part1': '74bfb1bf83529de44d2870aea5bcc924111af1d5c17b5c3a31a297fb52e1e668', 'payload.part2': 'da74d8bbd8aae5939a1c516bc5b1aaf2171d4125bd90a237edeb6a46b5e2e95f', 'payload.part3': 'e05f1bec28f6fa727bef7cfda4bc048ce85637ff77ecef0c8f76c14ce46a2894'}
for name, expected in EXPECTED.items():
    data = (Path(".bootstrap") / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise SystemExit(f"{name} checksum mismatch: {actual}")
print("bootstrap payload verified")
