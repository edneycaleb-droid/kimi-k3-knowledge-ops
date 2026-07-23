import hashlib
from pathlib import Path
P=1000003
E=[(6909, 592011, 37178, '6f17e1f7a30aae5c4cf4e9b0c1f8d2abb82e7118e1731984e47da384ee8821b1'), (6909, 590682, 941966, '74bfb1bf83529de44d2870aea5bcc924111af1d5c17b5c3a31a297fb52e1e668'), (6909, 589371, 380117, 'da74d8bbd8aae5939a1c516bc5b1aaf2171d4125bd90a237edeb6a46b5e2e95f'), (6909, 592209, 196573, 'e05f1bec28f6fa727bef7cfda4bc048ce85637ff77ecef0c8f76c14ce46a2894')]
for i,(n,a,w,h) in enumerate(E):
 p=Path(f".bootstrap/payload.part{i}"); b=bytearray(p.read_bytes())
 if len(b)!=n: raise SystemExit(f"payload {i} length {len(b)} != {n}")
 if hashlib.sha256(b).hexdigest()!=h:
  da=(a-sum(b))%P
  dw=(w-sum((j+1)*v for j,v in enumerate(b)))%P
  pos=(dw*pow(da,-1,P))%P
  if not 1<=pos<=n: raise SystemExit(f"payload {i} uncorrectable")
  delta=da if da<128 else da-P
  value=b[pos-1]+delta
  if not 0<=value<128: raise SystemExit(f"payload {i} invalid correction")
  b[pos-1]=value
  if hashlib.sha256(b).hexdigest()!=h: raise SystemExit(f"payload {i} checksum failure")
  p.write_bytes(b)
for p in Path(".bootstrap").glob("payload.tail*"): p.unlink()
print("bootstrap payload verified")
