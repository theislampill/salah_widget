"""Exercise actual publication guard helpers only; no Git/network effects."""
from pathlib import Path
import copy
import hashlib
import json
import commit_specification as commit
import publish_specification as publish

ROOT=Path(__file__).resolve().parents[1]


def main():
    checks=[]
    def check(name,expected,observed):
        assert observed==expected,(name,expected,observed)
        checks.append({'control':name,'expected':expected,'observed':observed,'pass':True})
    check('exact repository HTTPS',True,commit.origin_allowed('https://github.com/theislampill/salah_widget.git'))
    check('exact repository SSH',True,commit.origin_allowed('git@github.com:theislampill/salah_widget.git'))
    for url in ('https://github.com/another/salah_widget.git','https://github.com/theislampill/salah_widget-extra.git','https://github.com.evil.example/theislampill/salah_widget.git','file:///tmp/salah_widget'):
        check('reject other origin '+url,False,commit.origin_allowed(url))
    receipt={'number':2,'canonicalId':'R0002','revision':1,'sourceTarget':publish.TARGET,'specificationCommit':'a'*40,'commentSha256':'b'*64}
    check('matching existing receipt',True,publish.receipt_identity_matches(receipt,receipt))
    for key in receipt:
        bad=dict(receipt);bad[key]='DIFFERENT'
        check('reject copied receipt '+key,False,publish.receipt_identity_matches(bad,receipt))
    marker='<!-- TEST-MARKER -->';body='reviewed plan '+marker
    issue={'id':2,'title':'R0002 example','body':'Original obligation','state':'open'}
    packet={'issue':issue,'comments':[{'id':10,'body':'Earlier accepted proof'}]}
    comments=copy.deepcopy(packet['comments'])+[{'id':11,'body':body}]
    def error_count(target=publish.TARGET,current=issue,discussion=comments):
        return len(publish.poststate_errors(target,packet,current,discussion,marker,body,11))
    check('healthy post-publication state',0,error_count())
    cases=[('main drift',dict(target='c'*40)),
           ('changed issue body',dict(current={**issue,'body':'Amended'})),
           ('external issue closure',dict(current={**issue,'state':'closed'})),
           ('new discussion',dict(discussion=comments+[{'id':12,'body':'New owner decision'}])),
           ('deleted prior comment',dict(discussion=comments[1:])),
           ('edited prior comment',dict(discussion=[{'id':10,'body':'Changed'},comments[1]])),
           ('duplicate marker',dict(discussion=comments+[{'id':12,'body':body}]))]
    for name,kwargs in cases:check('reject '+name,True,error_count(**kwargs)>0)
    result={'result':'PASS','scope':'Pure guard calls with synthetic isolated objects only; no GitHub/Git write, product test or runtime evidence.',
            'checks':checks,'guardSources':{name:hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest() for name in ('commit_specification.py','publish_specification.py')},
            'consumerBinding':'Primary independent review checks that origin guard precedes Git writes, receipt guard precedes appending, and poststate guard runs after actual readbacks.'}
    (ROOT/'PUBLICATION_GUARD_CONTROLS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'controls':len(checks)}))


if __name__=='__main__':main()
