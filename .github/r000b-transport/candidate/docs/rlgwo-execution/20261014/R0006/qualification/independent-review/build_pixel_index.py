"""Join manually inspected original native frames to existing lossless receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    entries = []

    def add(engine, case, acquisition, observations, note=''):
        row = {'engine': engine, 'caseId': 'R0006-' + case, 'originalAcquisition': acquisition,
               'scope': 'first presented prayer-card state only', 'continuousClipCredit': False,
               'motionCredit': False, 'observedContinuityGaps': engine == 'firefox', 'observations': [], 'note': note}
        for kind, folder, ordinal, verdict, description in observations:
            receipt_path = HERE / folder / 'samples.json'
            receipt = json.loads(receipt_path.read_bytes())
            sample = next(s for s in receipt['samples'] if s['ordinal'] == ordinal)
            assert hashlib.sha256((HERE/folder/sample['png']).read_bytes()).hexdigest()==sample['pngSha256']
            if 'videoSha256' in row:
                assert row['videoSha256'] == receipt['videoSha256']
            row['videoSha256'] = receipt['videoSha256']
            row['nativeFrameCount'] = receipt['frameCount']
            row['originalFrameDimensions'] = receipt['size']
            row['observations'].append({'kind': kind, 'ordinal': ordinal, 'ptsSeconds': sample['ptsSeconds'],
                'verdict': verdict, 'finding': description, 'originalPngReceipt': str(receipt_path.relative_to(HERE)).replace('\\','/'),
                'originalPngReceiptSha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                'originalPng': folder + '/' + sample['png'], 'pngSha256': sample['pngSha256'], 'decodedWholeFrameRgbSha256': sample['decodedRgbSha256']})
        decisive = [o for o in row['observations'] if o['kind'] in ('first-current', 'first-promoted')]
        row['boundedVerdict'] = 'FAIL_FIRST_PRESENTATION' if any(o['verdict'] == 'FAIL' for o in decisive) else 'PASS_FIRST_PRESENTATION_ONLY'
        entries.append(row)

    def pair(engine, case, acquisition, folder, first, predecessor=None, verdict='PASS', description='All six rows, clocks, header/buckle, arc/next output and date footer are complete.'):
        observations = [('first-current', folder, first, verdict, description)]
        if predecessor is not None:
            observations.append(('predecessor', folder, predecessor, 'OBSERVED', 'Original preceding frame; inspected without substituting a later healthy image.'))
        add(engine, case, acquisition, observations)

    pair('chromium','cold-body','browser/chromium/R0006-cold-body','original-cold/chromium',1506,1505)
    for case, frame in [('frozen-recovery',1495),('hidden-resume',1633)]:
        pair('chromium',case,'browser/chromium/R0006-'+case,'first-native/chromium/R0006-'+case,frame,frame-1)
    for case, frame in [('cache-offline',4),('generation-late-cleanup',47),('offline-entry',74),('third-success',74)]:
        pair('chromium',case,'batch3/chromium/R0006-'+case,'batch3-first/R0006-'+case,frame,frame-1)
    add('chromium','cache-denied','batch3/chromium/R0006-cache-denied',[
        ('first-current','batch3-first/R0006-cache-denied',4,'PASS','Complete cached Fajr04:47 current card.'),
        ('first-refresh','batch3-first/R0006-cache-denied',35,'PASS','Complete healthy Fajr05:03 current card with denied persistence.'),
        ('predecessor','batch3-first/R0006-cache-denied',3,'OBSERVED','Blank startup frame.')])
    add('chromium','tomorrow-promotion','batch3/chromium/R0006-tomorrow-promotion',[
        ('first-current','batch3-first/R0006-tomorrow-promotion',5,'PASS','Complete initial Sep7 card.'),
        ('first-promoted','additional-first/promotion',1624,'PASS','Complete Sep8 card with Fajr05:00 next/countdown.'),
        ('promotion-predecessor','additional-first/promotion',1623,'OBSERVED','Sep7 current card.')])
    pair('chromium','accelerated-recovery','batch4/R0006-accelerated-recovery','additional-first/accelerated',1505,1504)
    pair('chromium','hidden-resume','batch8/chromium/R0006-hidden-resume','chromium-offscreen8-first',1636,1635)

    pair('firefox','cold-body','browser/firefox/R0006-cold-body','original-cold/firefox',1523,1522,'FAIL','First recovered text appears with a lower white region hiding Asr/Maghrib/Isha/footer.')
    add('firefox','cold-body','batch6/firefox/R0006-cold-body',[
        ('first-current','firefox-cold6-first',1519,'PASS','First current image complete; no later frame substitution.'),
        ('predecessor','firefox-cold6-first',1518,'OBSERVED','Wholly blank.'),
        ('body-pending-loading','firefox-cold6-states',50,'PASS','At2s body1 pending: complete honest six em-dash rows and unavailable dates.'),
        ('exhausted-unavailable','firefox-cold6-states',1000,'PASS','At40s after native three-attempt exhaustion: complete truthful unavailable card.'),
        ('early-font-state','firefox-cold6-first',16,'FAIL','First loading card lacks row/footer labels while font request waits.'),
        ('post-recovery-gap','firefox-cold6-first',1522,'FAIL','Wholly blank recovered-state video frame. No continuous-readability credit.')])
    for case, frame in [('frozen-recovery',1515),('accelerated-recovery',1511),('cache-offline',17),('generation-late-cleanup',57),('offline-entry',80),('third-success',82)]:
        pair('firefox',case,'batch6/firefox/R0006-'+case,'batch6-first/R0006-'+case,frame,frame-1)
    add('firefox','cache-denied','batch6/firefox/R0006-cache-denied',[
        ('first-current','batch6-first/R0006-cache-denied',16,'FAIL','Lower white region hides Maghrib/Isha/footer.'),
        ('predecessor','batch6-first/R0006-cache-denied',15,'OBSERVED','Wholly blank.'),
        ('subsequent-font-state','batch6-first/R0006-cache-denied',17,'FAIL','Labels/time/footer disappear during font request.'),
        ('first-refresh','batch6-first/R0006-cache-denied',44,'PASS','Complete healthy refresh; does not replace failed initial current image.')])
    add('firefox','tomorrow-promotion','batch6/firefox/R0006-tomorrow-promotion',[
        ('first-current','batch6-first/R0006-tomorrow-promotion',18,'FAIL','Lower white region hides Maghrib/Isha/footer.'),
        ('first-promoted','batch6-first/R0006-tomorrow-promotion',1664,'FAIL','Upper white region hides header/arc/next/Fajr; first visible Sep8 portion only.'),
        ('promotion-predecessor','batch6-first/R0006-tomorrow-promotion',1663,'OBSERVED','Wholly blank.')])
    pair('firefox','hidden-resume','batch8/firefox/R0006-hidden-resume','firefox-offscreen8-first',1641,1640)
    add('firefox','cache-denied','batch9/firefox/R0006-cache-denied',[
        ('first-current','firefox-denied9-first',18,'PASS','Complete initial cached Fajr04:47 current card.'),
        ('first-refresh','firefox-denied9-first',43,'PASS','Complete healthy Fajr05:03 card; persistence denied.'),
        ('predecessor','firefox-denied9-first',17,'OBSERVED','Wholly blank.')])
    add('firefox','tomorrow-promotion','batch10/firefox/R0006-tomorrow-promotion',[
        ('first-current','firefox-promotion10-first',18,'PASS','Complete initial Sep7 current card.'),
        ('first-promoted','firefox-promotion10-first',1632,'FAIL','White upper region hides header, most arc, Isha label and05:00 next value; only bottom of arc/countdown, six rows and Sep8 footer visible.'),
        ('promotion-predecessor','firefox-promotion10-first',1631,'OBSERVED','Blank card region; no earlier complete promoted image in transition sheets.')])

    add('firefox','tomorrow-promotion','batch11/firefox/R0006-tomorrow-promotion',[
        ('first-current','firefox-promotion11-first',25,'PASS','Complete initial Sep7 current card.'),
        ('first-promoted','firefox-promotion11-first',1627,'PASS','Complete Sep8 header/arc/Isha, Fajr05:00 next/countdown, six rows and date footer.'),
        ('initial-predecessor','firefox-promotion11-first',24,'OBSERVED','Blank startup before the first current image.'),
        ('promotion-predecessor','firefox-promotion11-first',1626,'OBSERVED','Complete Sep7 card.')],
        'Headed existing video-only route with native100ms observation polling; exact one-case packet bound separately. No whole-clip or motion qualification follows from these bounded windows.')
    entries[-1]['observedContinuityGaps'] = None

    selection_path=HERE.parent/'selection.json'
    selection=json.loads(selection_path.read_bytes())
    by_source={r['source']:r for r in selection}
    selected_count=0
    for entry in entries:
        record=by_source.get(entry['originalAcquisition'])
        entry['selected']=bool(record and record['status'].startswith('SELECTED'))
        entry['publicDestination']=record['destination'] if record else None
        if entry['selected']:
            selected_count+=1
            assert entry['boundedVerdict']=='PASS_FIRST_PRESENTATION_ONLY'
    assert selected_count==20

    packet = {'schema':'r0006-independent-native-pixel-index/v1','status':'PASS_SELECTED_FIRST_PRESENTATION_ONLY',
        'sourceBase':'c431733c57f76e2b441ee8f8cd85a1fa6675de55',
        'scope':'Original native frame inspection and selected acquisition binding complete for the pre-delivery candidate. Exact committed-head/public readback and A07 delivery remain separate.',
        'reviewerEffects':'Read-only source/evidence; wrote reports and offline media only under independent-review.',
        'clockLimit':'PTS is native video time, not fixture performance elapsed time; unique DOM ordinal-to-frame association not asserted.',
        'continuousGate':'No fresh functional clip receives continuous or motion credit. Exact retained original preservation controls supply their separately qualified30s gate.',
        'selectionSha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(), 'selectedCount':selected_count,
        'entries':entries}
    (HERE/'native-pixel-index.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8')
    print(len(entries),'acquisitions;',sum(e['boundedVerdict']=='FAIL_FIRST_PRESENTATION' for e in entries),'retained failed first presentations')


if __name__=='__main__':main()
