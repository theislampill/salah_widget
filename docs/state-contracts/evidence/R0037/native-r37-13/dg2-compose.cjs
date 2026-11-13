const path = require("path"), fs = require("fs");
const { chromium } = require(path.join(process.argv[2], "playwright"));
const raw = process.argv[3], out = process.argv[4];
fs.mkdirSync(out, { recursive: true });
const url = f => "data:image/png;base64," + fs.readFileSync(path.join(raw, f)).toString("base64");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 700 } });
  await p.route("**/*", r => r.abort());
  await p.setContent('<body style="margin:0;background:#8a8f99"><canvas id=k></canvas></body>');
  const stats = await p.evaluate(async ([h, c]) => {
    const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = s; });
    const H = await load(h), C = await load(c), W = H.width, Ht = H.height;
    const px = im => { const cv = document.createElement("canvas"); cv.width = W; cv.height = Ht; const x = cv.getContext("2d"); x.drawImage(im, 0, 0); return x.getImageData(0, 0, W, Ht); };
    const a = px(H), d = px(C), diff = new ImageData(W, Ht); let n = 0, n8 = 0;
    for (let i = 0; i < a.data.length; i += 4) {
      let m = 0; for (let k = 0; k < 3; k++) m = Math.max(m, Math.abs(a.data[i + k] - d.data[i + k]));
      const g = 235; diff.data[i] = g; diff.data[i + 1] = g; diff.data[i + 2] = g; diff.data[i + 3] = 255;
      if (m) { n++; if (m > 8) n8++; const t = Math.min(1, 0.35 + m / 40); diff.data[i] = 255; diff.data[i + 1] = Math.round(235 * (1 - t)); diff.data[i + 2] = Math.round(235 * (1 - t)); }
    }
    const pad = 30, top = 70, k = document.getElementById("k"); k.width = pad * 4 + W * 3; k.height = top + Ht + 70;
    const x = k.getContext("2d"); x.fillStyle = "#8a8f99"; x.fillRect(0, 0, k.width, k.height);
    x.drawImage(H, pad, top); x.drawImage(C, pad * 2 + W, top);
    const dc = document.createElement("canvas"); dc.width = W; dc.height = Ht; dc.getContext("2d").putImageData(diff, 0, 0); x.drawImage(dc, pad * 3 + W * 2, top);
    x.strokeStyle = "#ffff00"; x.setLineDash([4, 3]);
    x.strokeRect(pad + 0.5, top + 0.5, 330, 534); x.strokeRect(pad * 2 + W + 0.5, top + 0.5, 325, 530); x.strokeRect(pad * 3 + W * 2 + 0.5, top + 0.5, 325, 530);
    x.fillStyle = "#000"; x.font = "bold 18px Arial";
    x.fillText("A: 330×534 iframe (README V1 today)", pad, 30); x.fillText("B: 325×530 iframe (DG2 option B)", pad * 2 + W, 30); x.fillText("Difference A vs B (red = differs)", pad * 3 + W * 2, 30);
    x.font = "14px Arial";
    x.fillText("Frozen V1 card, same fixtures/clock; page background #8a8f99; dashed = iframe box", pad, 54);
    x.fillText(n + " px differ in total; 3,105 inside the card box", pad * 3 + W * 2, 54);
    x.fillText("A shows the card's own box-shadow (0 18px 50px #0008) in the corner cut-outs and the 5×4 margin; B's rounded clip removes it.", pad, top + Ht + 30);
    x.fillText("Small differences (mostly 1–2 levels) in backdrop-filter glass: header pill, prayer-row ends (cause not traced; not visible).", pad, top + Ht + 52);
    return { W, Ht, n, n8, png: k.toDataURL("image/png") };
  }, [url("historical.png"), url("canonical.png")]);
  fs.writeFileSync(path.join(out, "r0037-dg2-side-by-side.png"), Buffer.from(stats.png.split(",")[1], "base64"));
  fs.copyFileSync(path.join(raw, "historical.png"), path.join(out, "r0037-dg2-A-330x534.png"));
  fs.copyFileSync(path.join(raw, "canonical.png"), path.join(out, "r0037-dg2-B-325x530.png"));
  // standalone difference map, 3x zoom of the two corners
  await p.setContent('<body style="margin:0"><canvas id=z></canvas></body>');
  const z = await p.evaluate(async ([h, c]) => {
    const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = s; });
    const H = await load(h), C = await load(c), k = document.getElementById("z"); k.width = 2 * 90 * 4 + 90; k.height = 2 * 80 * 4 + 110;
    const x = k.getContext("2d"); x.fillStyle = "#8a8f99"; x.fillRect(0, 0, k.width, k.height); x.imageSmoothingEnabled = false;
    x.fillStyle = "#000"; x.font = "bold 16px Arial"; x.fillText("A 330×534", 10, 22); x.fillText("B 325×530", 90 * 4 + 60, 22);
    x.font = "13px Arial"; x.fillText("4× zoom: top-left corner (top) and bottom-right corner + margin (bottom)", 10, 42);
    x.drawImage(H, 0, 0, 80, 70, 10, 55, 320, 280); x.drawImage(C, 0, 0, 80, 70, 90 * 4 + 60, 55, 320, 280);
    x.drawImage(H, 260, 470, 80, 70, 10, 345, 320, 280); x.drawImage(C, 260, 470, 80, 70, 90 * 4 + 60, 345, 320, 280);
    return k.toDataURL("image/png");
  }, [url("historical.png"), url("canonical.png")]);
  fs.writeFileSync(path.join(out, "r0037-dg2-corners-4x.png"), Buffer.from(z.split(",")[1], "base64"));
  console.log(JSON.stringify({ W: stats.W, H: stats.Ht, changed: stats.n, over8: stats.n8 }));
  await b.close();
})();
