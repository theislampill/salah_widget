// A single owner supplies two consecutive complete RGBA presentation images.
// Advance the previous image only after every write succeeds. The owner must
// invalidate it after resize, external paint, replacement or a partial failure.
export function changedRectangles(before, after, width, height, tile = 16) {
  const length = width * height * 4;
  if (![width, height, tile].every(value => Number.isSafeInteger(value) && value > 0)
      || !(after instanceof Uint8ClampedArray) || after.length !== length
      || (before !== null && (!(before instanceof Uint8ClampedArray) || before.length !== length))) {
    throw new RangeError('Two complete RGBA images of the declared size are required');
  }
  if (before === null) return [{x: 0, y: 0, width, height}];
  const rectangles = [];
  for (let top = 0; top < height; top += tile) {
    for (let left = 0; left < width; left += tile) {
      let minX = width, minY = height, maxX = -1, maxY = -1;
      for (let y = top; y < Math.min(height, top + tile); y++) {
        for (let x = left; x < Math.min(width, left + tile); x++) {
          const i = 4 * (y * width + x);
          if (before[i] === after[i] && before[i+1] === after[i+1]
              && before[i+2] === after[i+2] && before[i+3] === after[i+3]) continue;
          minX = Math.min(minX, x); maxX = Math.max(maxX, x);
          minY = Math.min(minY, y); maxY = y;
        }
      }
      if (maxY >= 0) rectangles.push({x: minX, y: minY, width: maxX-minX+1, height: maxY-minY+1});
    }
  }
  return rectangles;
}

export class PresentationWriter {
  constructor(context, arm, tile = 16) {
    if (!['full', 'changed'].includes(arm)) throw new RangeError('Unknown write arm');
    this.context = context; this.arm = arm; this.tile = tile; this.invalidate();
  }
  invalidate() { this.previous = null; }
  publish(image) {
    if (this.width !== image.width || this.height !== image.height) this.invalidate();
    const rectangles = this.arm === 'full'
      ? [{x: 0, y: 0, width: image.width, height: image.height}]
      : changedRectangles(this.previous, image.data, image.width, image.height, this.tile);
    try {
      for (const r of rectangles) {
        if (r.width === image.width && r.height === image.height) this.context.putImageData(image, 0, 0);
        else this.context.putImageData(image, 0, 0, r.x, r.y, r.width, r.height);
      }
    } catch (error) { this.invalidate(); throw error; }
    if (this.arm === 'changed') {
      // The producer may recycle ImageData immediately after publication.
      if (!this.previous) this.previous = image.data.slice();
      else for (const r of rectangles) for (let y = r.y; y < r.y + r.height; y++) {
        const start = 4*(y*image.width+r.x);
        this.previous.set(image.data.subarray(start, start+4*r.width), start);
      }
    }
    this.width = image.width; this.height = image.height;
    return {writes: rectangles.length, pixels: rectangles.reduce((n,r) => n + r.width*r.height, 0)};
  }
}
