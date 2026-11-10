/** CP9 donor-derived responsiveness invariant: optional physical rendering may not
 * occupy the prayer/settings UI thread when worker execution is unavailable.
 * CP7's reference client remains unchanged; this is the native host policy only.
 */
export function requireNativeWorker(_pack){
 throw new Error('Native physical-sky worker unavailable; visual withdrawn to preserve prayer responsiveness. Retry real-sky assets to restart the worker.');
}
