"""Score sealed human answer sheets by participant and condition, without aggregating unlike axes."""
import argparse,csv,json,itertools
from collections import Counter,defaultdict
from pathlib import Path

OPTIONS=("dry","drizzle","light","moderate","heavy","showers","cannot tell")


from lossless_pack import DESIGNS, canonical, digest, treatments, require
from cryptography.hazmat.primitives import serialization


def score(key,answers,signed,public_key,design,mapping_commitment):
    pack=signed["manifest"]
    public_key.verify(bytes.fromhex(signed["signature"]),canonical(pack))
    commitment=mapping_commitment["commitment"]
    public_key.verify(bytes.fromhex(mapping_commitment["signature"]),canonical(commitment))
    require(commitment.get("schema")=="r0040-blind-mapping/1" and
            commitment.get("mappingSha")==digest(canonical(key)) and
            commitment.get("manifestSha")==digest(canonical(pack)) and
            commitment.get("evidenceClass")==key.get("evidenceClass")==pack.get("evidenceClass"),
            "blind mapping differs from its pre-collection custodian commitment")
    require(design in DESIGNS and key["design"]==pack["design"]==design and
            [key["engine"]]==pack["engines"] and key["pins"]==pack["pins"] and
            key["manifestSha"]==digest(canonical(pack)),"wrong design, source pins or signed manifest")
    cells={c["blindId"]:c for c in key["cells"]}
    population=set()
    for c in key["cells"]:
        ident=(key["engine"],c["block"],c["condition"],c["model"],c["treatment"])
        require(pack["cells"].get("/".join(ident),{}).get("log")==c["captureLog"],"substituted treatment/receipt")
        population.add(ident)
    require(len(key["cells"])==len(cells)==len(population) and population==treatments(design,(key["engine"],)),
            "incomplete/duplicate/wrong blind design")
    people=defaultdict(dict)
    for a in answers:
        who=a["participant"];blind=a["blindId"];recognition=a["recognition"]
        if not who or blind not in cells or blind in people[who] or recognition not in OPTIONS:
            raise ValueError("invalid or duplicate response")
        n=int(a["naturalness"])
        if n not in range(1,6):raise ValueError("naturalness outside 1–5")
        people[who][blind]=(recognition,n)
    if len(people)<5 or any(set(cells)!=set(v) for v in people.values()):
        raise ValueError("five complete independent-participant records required; independence verified by coordinator")
    result=[]
    for who,rows in sorted(people.items()):
        matrix=defaultdict(Counter);ratings=defaultdict(list)
        for blind,(answer,n) in rows.items():
            c=cells[blind];facet=(c["block"],c["model"],c["treatment"],c["condition"])
            matrix[facet][answer]+=1;ratings[facet].append(n)
        for (block,model,treatment,condition),answers in sorted(matrix.items()):
            result.append({"evidenceClass":pack["evidenceClass"],"participant":who,"block":block,"model":model,"treatment":treatment,"condition":condition,"responses":answers,
                "dryFalseAlarms":sum(v for k,v in answers.items() if k not in ("dry","cannot tell")) if condition=="dry" else None,
                "correct":answers[condition],"cannotTell":answers["cannot tell"],"naturalnessRatings":ratings[(block,model,treatment,condition)]})
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("key",type=Path);p.add_argument("answers",type=Path)
    p.add_argument("signed_manifest",type=Path);p.add_argument("trusted_public_key",type=Path);p.add_argument("--design",required=True,choices=DESIGNS)
    p.add_argument("--mapping-commitment",type=Path,required=True,help="independently retained signed commitment distributed before collecting responses")
    args=p.parse_args()
    with args.answers.open(newline="") as f:print(json.dumps(score(json.loads(args.key.read_bytes()),csv.DictReader(f),json.loads(args.signed_manifest.read_bytes()),serialization.load_pem_public_key(args.trusted_public_key.read_bytes()),args.design,json.loads(args.mapping_commitment.read_bytes())),indent=2))
