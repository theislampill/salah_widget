/* Capture-only identity pixels outside the unchanged 330x534 iframe/card. */
(() => {
  if (window !== top) return;
  let childMarker = null;
  window.addEventListener('message', event => {
    const data = event.data;
    if (event.source !== window.frames[0] || data?.kind !== 'salah-startup-pixel-marker/1' ||
      !/^[0-9a-f]{32}$/.test(data.token)) return;
    childMarker = data;
  });
  const install = () => {
    if (!document.body) return false;
    const el = document.createElement('canvas'); el.width = 30; el.height = 512;
    el.style = 'position:fixed;left:360px;top:0;width:30px;height:512px;z-index:2147483647;pointer-events:none';
    document.body.append(el); const c = el.getContext('2d');
    let lastToken = null;
    function tick() {
      const marker = window.SalahStartupTiming?.marker() || childMarker;
      const currentToken = marker && /^[0-9a-f]{32}$/.test(marker.token) ? marker.token : null;
      if (currentToken !== lastToken) {
        c.clearRect(0, 0, 30, 512);
      }
      if (currentToken !== lastToken && currentToken !== null) {
        c.fillStyle = '#ff00ff'; c.fillRect(0, 0, 30, 512);
        for (let wordIndex = 0; wordIndex < 4; wordIndex++) {
          const word = Number.parseInt(marker.token.slice(wordIndex*8, wordIndex*8+8), 16);
          for (let bit = 0; bit < 32; bit++) {
            c.fillStyle = (word >>> bit) & 1 ? 'white' : 'black';
            const index=wordIndex*32+bit;
            c.fillRect(4+(index%2)*13, Math.floor(index/2)*8, 13, 8);
          }
        }
      }
      lastToken = currentToken;
      requestAnimationFrame(tick);
    }
    tick(); return true;
  };
  if (!install()) {
    const observer = new MutationObserver(() => {if (install()) observer.disconnect();});
    observer.observe(document, {childList:true, subtree:true});
  }
})();
