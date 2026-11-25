"""Read-only inventory of the original packs. Output hashes, never a key or participant-facing media."""
import argparse
import hashlib
import json
from pathlib import Path


PACKS = {"blind-pack":(90,"LIMITATION.md"),"blind-pack-controlled":(144,"SUPERSEDED.md"),
         "blind-pack-controlled-declared-gain":(180,None)}


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root,keys,protocol):
    result={}
    for (name,(count,note)),key in zip(PACKS.items(),keys,strict=True):
        folder=root/name
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("missing original "+name)
        items=sorted(folder.rglob("*"))
        if any(p.is_symlink() for p in items):
            raise ValueError("symlink in "+name)
        files={p.relative_to(folder).as_posix():sha(p) for p in items if p.is_file()}
        if sum(n.lower().endswith((".webp",".webm",".mp4",".mkv")) for n in files)!=count or (note and note not in files):
            raise ValueError("unexpected clip count or missing limitation note in "+name)
        if key.is_symlink() or any(key.resolve().is_relative_to((root/n).resolve()) for n in PACKS):
            raise ValueError("key must be a separate regular file outside all packs")
        # A fresh inventory digest binds filenames and note bytes. Historic manifest recipes may differ.
        result[name]={"files":files,"inventorySha256":hashlib.sha256(json.dumps(files,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                      "keySha256":sha(key)}
    if protocol.is_symlink() or not protocol.is_file():
        raise ValueError("original protocol unavailable")
    return {"packs":result,"protocolSha256":sha(protocol),"historicalManifestVerified":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("parent",type=Path);p.add_argument("protocol",type=Path)
    p.add_argument("keys",type=Path,nargs=3,help="original sealed keys, in 90/144/180 order; no writes")
    args=p.parse_args()
    print(json.dumps(inventory(args.parent,args.keys,args.protocol),indent=2))
