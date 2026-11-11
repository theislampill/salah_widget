/* Full Moon-wrapper replay over a live runtime is unsupported (R0021 ES21-05,
 * owner decision 2026-11-11). This unit is first in the generated host wrapper,
 * so the refusal precedes every resource and global replacement, including the
 * initial receiver. First boot, installWorkerSource refinement and retry are the
 * supported routes; a wrapper may install again only after the runtime retired. */
if(window.SalahMoonRuntime&&!window.SalahMoonRuntime.disposed)throw new Error('Moon wrapper replay refused: a live Moon runtime is installed');
