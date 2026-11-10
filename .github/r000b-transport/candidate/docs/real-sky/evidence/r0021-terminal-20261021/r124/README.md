# Chromium resource result: preview only

The original r123 resource observer failed before native decode: its empty-array `find` never called the image-registration predicate, so `started++` dereferenced an absent record. This was an acquisition defect, not a widget failure. The original calls/profile and failed slot remain under [r123](../r123/).

r124 consumed the continuation's **one permitted acquisition repeat**, after independent diagnosis/admission and an offline observer control. The corrected observer retained the actual native `Image.decode` Promise. Three preview-owner changed/cancel/recovery cycles and terminal disposal completed, with 23 native decodes settled, actual invalid-image rejection, stale-reaction rejection, cached recovery reuse and cleared roots. [Independent result](../reviews/resources-r124-partial-result-review-r1.json).

After releasing the held sky module, the runner attempted to dereference a still-null sky state and stopped. This is a second acquisition defect. **The Chromium refined-owner resource sequence is INCOMPLETE.** No further repeat was run or authorized. The successful preview sequence does not stand in for that instance or for whole-browser resource qualification.

The exact observer, failed predecessor, control and runners are published under [terminal inputs](../terminal-inputs/cost/). The failed results are retained; they are not widget performance failures. The separate r122 product cleanup defect remains blocking.
