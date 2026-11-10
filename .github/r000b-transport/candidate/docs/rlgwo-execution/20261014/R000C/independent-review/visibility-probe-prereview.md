# Independent bounded visibility diagnostic prereview

The single reduced headed 20-second diagnostic is justified by the observed stopped-render/recovery gap and current source visibility gate. It is not a qualification retry and grants no C16 credit.

I read the complete private wrapper `../visibility_probe.py`, SHA256 `9d4b7cc44a888aed71224f7566763aeee36e0edccf48cefb09e5005716679e90`, and verified the unchanged driver `76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce` and packet `268d820ff632135eb86ed92f3650b619cac71440eef2e282605d00dcd4749f67`.

The wrapper calls the original wait function and changes behavior only after the exact original READY predicate succeeds. It adds a labeled native visibilitychange listener and samples native document visibility/hidden, product-owned paused class, actual card/viewport geometry, existing global loop-started and last-render summary, admitted amount, request timestamps/busy flag and native fixture ledger. The sampler does not call qaState, model, render, fetchWeather or lunar getters, force native flags, or read inaccessible `_raf`/`_onScreen` closure variables. The unchanged original READY still has its already disclosed diagnostic reads.

Twenty-one passive samples span twenty host seconds, after which the deliberate diagnostic exception ends the original driver before either acceptance watch. Its acquisition status remains FAIL; a separate diagnostic binding records completion, driver exit status, exact probe digest and override. Preserve the exact invocation, full native original and all raw samples. This review applies to one reduced headed context using the already pinned input and host-wait/boundary configuration; it does not authorize an expanded case matrix.

The result can discriminate native hidden/paused/inactive state from an active render loop with blank captured pixels. It cannot establish a renderer/capturer cause merely from timing coincidence. A failure to capture the desired history remains incomplete diagnostic evidence, without automatic repetition or acceptance credit.
