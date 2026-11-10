"""Read-only exact public projection and lossless compression reconciliation."""
import gzip
import hashlib
import json
import lzma
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIVATE=HERE.parent
SOURCE=PRIVATE.parent/'salah_widget'
PUBLIC=SOURCE/'docs/rlgwo-execution/20261014/R0006'


def digest_stream(stream):
    value=hashlib.sha256();size=0
    for block in iter(lambda:stream.read(1048576),b''):
        value.update(block);size+=len(block)
    return value.hexdigest(),size


def digest_file(path):
    with path.open('rb') as stream:return digest_stream(stream)


def main():
    failures=[]
    def check(ok,message):
        if not ok:failures.append(message)
    manifest=json.loads((PUBLIC/'manifest.json').read_bytes())
    named=set();total=0
    for record in manifest['files']:
        relative=record['path'];path=PUBLIC/relative
        check(path.resolve().is_relative_to(PUBLIC.resolve()),'manifest path escape '+relative)
        check(relative not in named,'duplicate member '+relative);named.add(relative)
        actual,size=digest_file(path);total+=size
        check(actual==record['sha256'] and size==record['bytes'],'manifest byte drift '+relative)
    actual_files={str(p.relative_to(PUBLIC)).replace('\\','/') for p in PUBLIC.rglob('*') if p.is_file()}
    extras=sorted(actual_files-named-{'manifest.json'})
    check(not extras,'unmanifested files '+repr(extras))
    proof=json.loads((PUBLIC/'cases.json').read_bytes())
    selection=json.loads((PRIVATE/'selection.json').read_bytes())
    check(proof['schema']=='r0006-native-proof/v1','native proof schema differs')
    check(len(proof['acquisitions'])==len(selection),'acquisition denominator differs')
    by_source={r['source']:r for r in selection}
    roundtrips=[];selected=0
    for acquisition in proof['acquisitions']:
        original=PRIVATE/acquisition['acquisitionId'];declared=by_source[acquisition['acquisitionId']]
        check(acquisition['destination']==declared['destination'] and acquisition['status']==declared['status'],'selection mapping differs '+acquisition['acquisitionId'])
        if acquisition['status'].startswith('SELECTED'):
            selected+=1;check(not acquisition['missingArtifacts'],'selected required artifacts missing '+acquisition['acquisitionId'])
        for member in acquisition['members']:
            path=PUBLIC/member['path'];actual,size=digest_file(path)
            check(actual==member['sha256'],'member compressed bytes differ '+member['path'])
            mode=member['compression']
            opener=lzma.open if mode=='xz' else gzip.open if mode=='gzip' else open
            with opener(path,'rb') as stream:restored,count=digest_stream(stream)
            check(restored==member['originalSha256'] and count==member['originalBytes'],'lossless roundtrip differs '+member['path'])
            relative=Path(member['path']).relative_to(acquisition['destination'])
            if mode!='none':relative=relative.with_suffix('')
            source=next((original/'video').glob('*.webm')) if str(relative)=='native.webm' else original/relative
            check(source.is_file(),'original member absent '+str(source))
            if source.is_file():
                original_sha,original_size=digest_file(source)
                check(original_sha==restored and original_size==count,'restored member differs from original acquisition '+member['path'])
            if mode!='none':roundtrips.append({'path':member['path'],'compressedSha256':actual,'compressedBytes':size,'originalSha256':restored,'originalBytes':count})
    check(selected==20,'selected acquisitions not20')
    pixels=json.loads((HERE/'native-pixel-index.json').read_bytes())
    selected_pixels=[r for r in pixels['entries'] if r['selected']]
    check(len(selected_pixels)==selected,'selected pixel denominator differs')
    for row in selected_pixels:
        acquisition=next(a for a in proof['acquisitions'] if a['acquisitionId']==row['originalAcquisition'])
        video=next(m for m in acquisition['members'] if m['path'].endswith('/native.webm'))
        check(video['originalSha256']==row['videoSha256'],'pixel/video binding differs '+row['originalAcquisition'])
        check(row['boundedVerdict']=='PASS_FIRST_PRESENTATION_ONLY','selected first image failed '+row['originalAcquisition'])
    for filename in ('R0006-spec.md','issue-body.md','accepted-audit.md'):
        check((PUBLIC/'authority'/filename).read_bytes()==(PRIVATE/'authority'/filename).read_bytes(),'authority bytes drift '+filename)
    with lzma.open(PUBLIC/'authority/accepted-assessment.json.xz','rb') as stream:
        check(stream.read()==(PRIVATE/'authority/accepted-assessment.json').read_bytes(),'assessment bytes drift')
    docs=json.loads((PUBLIC/'qualification/docs-review.json').read_bytes())
    check(docs['schema']=='r0006-docs/v1','docs schema differs')
    check(docs['readmeSha256']==digest_file(SOURCE/'README.md')[0] and all(docs['checks'].values()),'docs receipt mismatch')
    certificate=json.loads((PUBLIC/'qualification/closure-certificate.json').read_bytes())
    check(certificate['schema']=='r0006-closure-certificate/v1' and certificate['phase']=='PRE_DELIVERY','certificate scope differs')
    check(not certificate['closeR0006Issued'] and not certificate['issueVerifiedClosed'] and certificate['deliveryProof'] is None,'premature delivery or closure claim')
    report={'schema':'r0006-independent-projection-review/v1','status':'PASS_CURRENT_PROJECTION' if not failures else 'FAIL',
            'manifestSha256':digest_file(PUBLIC/'manifest.json')[0],'nativeProofSha256':digest_file(PUBLIC/'cases.json')[0],
            'certificateSha256':digest_file(PUBLIC/'qualification/closure-certificate.json')[0],
            'fileCount':len(named),'totalNamedBytes':total,'acquisitions':len(selection),'selectedAcquisitions':selected,
            'compressedRoundtrips':roundtrips,'selectedPixelVideoJoins':len(selected_pixels),'failures':failures,
            'scope':'Local exact projection only. Final added review/certificate updates, final Git head and independent public readback remain separate.'}
    (HERE/'public-projection-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','manifestSha256','fileCount','totalNamedBytes','acquisitions','selectedAcquisitions','selectedPixelVideoJoins','failures')},indent=2))
    return bool(failures)


if __name__=='__main__':raise SystemExit(main())
