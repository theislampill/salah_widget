"""Make blinded copies of the original PNGs from a verified, signed single-engine pack."""
import argparse,csv,json,secrets,shutil,tempfile
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey,Ed25519PrivateKey
from lossless_pack import DESIGNS,ENGINES,canonical,digest,manifest,require


def prepare(root,engine,public_key,out,key_dir,design,pins,mapping_private_key):
    require(not out.exists() and not key_dir.exists() and not key_dir.is_relative_to(out) and
            not out.is_relative_to(key_dir) and not out.is_relative_to(root) and not key_dir.is_relative_to(root),
            "use separate new output and key directories, outside original evidence")
    pack=manifest(root,(engine,),design,pins)
    signed=json.loads((root/"signed-manifest.json").read_bytes())
    require(canonical(pack)==canonical(signed["manifest"]),"signature manifest mismatch")
    key=serialization.load_pem_public_key(public_key.read_bytes())
    require(isinstance(key,Ed25519PublicKey),"trusted Ed25519 public key required")
    key.verify(bytes.fromhex(signed["signature"]),canonical(pack))
    signer=serialization.load_pem_private_key(mapping_private_key.read_bytes(),password=None)
    require(isinstance(signer,Ed25519PrivateKey) and
            signer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)==
            key.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw),
            "mapping signer must match the independently trusted pack custodian")
    # Private working directories: an incomplete export is never presented as complete.
    cells=list(pack["cells"].items());secrets.SystemRandom().shuffle(cells)
    with tempfile.TemporaryDirectory(dir=out.parent) as scratch, tempfile.TemporaryDirectory(dir=key_dir.parent) as sealed:
        media=Path(scratch)/"media";media.mkdir()
        private=Path(sealed)/"key";private.mkdir()
        blind=[]
        for name,entry in cells:
            _,block,condition,model,treatment=name.split("/")
            ident=secrets.token_hex(10);dest=media/ident;dest.mkdir()
            src=root/entry["dir"];raw=(src/"capture.json").read_bytes();log=json.loads(raw)
            require(digest(raw)==entry["log"],"capture log changed after verification")
            ts=[f["t"] for f in log["frames"]]
            for frame in log["frames"]:
                contents=(src/frame["file"]).read_bytes()
                require(digest(contents)==frame["sha256"],"frame changed after verification")
                (dest/frame["file"]).write_bytes(contents)
            (dest/"timing.json").write_text(json.dumps([round(t-ts[0],5) for t in ts]))
            blind.append({"blindId":ident,"block":block,"condition":condition,"model":model,"treatment":treatment,"captureLog":entry["log"]})
        mapping={"schema":1,"evidenceClass":pack["evidenceClass"],"design":design,"engine":engine,"manifestSha":digest(canonical(pack)),"pins":pins,"cells":blind}
        (private/"key.json").write_text(json.dumps(mapping,indent=2))
        # Commitment must be retained/distributed before answers are collected.
        # It binds the exact random mapping without disclosing the sealed key.
        commitment={"schema":"r0040-blind-mapping/1","evidenceClass":pack["evidenceClass"],
                    "manifestSha":mapping["manifestSha"],"mappingSha":digest(canonical(mapping))}
        committed={"commitment":commitment,"signature":signer.sign(canonical(commitment)).hex()}
        (private/"mapping-commitment.json").write_bytes(canonical(committed))
        (media/"mapping-commitment.json").write_bytes(canonical(committed))
        with (media/"answers.csv").open("w",newline="") as stream:
            writer=csv.writer(stream);writer.writerow(["participant","blindId","recognition","naturalness"])
            for row in blind:writer.writerow(["",row["blindId"],"",""])
        private.rename(key_dir)
        media.rename(out)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("root",type=Path);p.add_argument("engine",choices=ENGINES)
    p.add_argument("public_key",type=Path);p.add_argument("out",type=Path);p.add_argument("key_dir",type=Path)
    p.add_argument("--design",required=True,choices=DESIGNS);p.add_argument("--pins",type=Path,required=True)
    p.add_argument("--mapping-key",type=Path,required=True,help="external trusted custodian private key; signs the exact blind mapping before distribution")
    a=p.parse_args();prepare(a.root.resolve(),a.engine,a.public_key,a.out.resolve(),a.key_dir.resolve(),a.design,json.loads(a.pins.read_bytes()),a.mapping_key)
