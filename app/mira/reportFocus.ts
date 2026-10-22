import { PixelRatio } from 'react-native';

let seq = 0;

export type Bounds = { x: number; y: number; w: number; h: number };

export function reportFocus(screen: string, elementId: string, bounds?: Bounds): void {
  if (!__DEV__) return;
  seq += 1;
  const r = PixelRatio.get();
  const b = bounds ?? { x: 0, y: 0, w: 0, h: 0 };
  const safeX = typeof b.x === 'number' && !isNaN(b.x) ? Math.round(b.x * r) : 0;
  const safeY = typeof b.y === 'number' && !isNaN(b.y) ? Math.round(b.y * r) : 0;
  const safeW = typeof b.w === 'number' && !isNaN(b.w) ? Math.round(b.w * r) : 0;
  const safeH = typeof b.h === 'number' && !isNaN(b.h) ? Math.round(b.h * r) : 0;
  console.log(
    'MIRA_FOCUS ' +
      JSON.stringify({
        seq,
        screen,
        element_id: elementId,
        bounds: {
          x: safeX,
          y: safeY,
          w: safeW,
          h: safeH,
        },
        ts: Date.now(),
      }),
  );
}
