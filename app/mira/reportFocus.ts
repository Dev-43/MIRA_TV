import { PixelRatio } from 'react-native';

let seq = 0;

export type Bounds = { x: number; y: number; w: number; h: number };

export function reportFocus(screen: string, elementId: string, bounds?: Bounds): void {
  if (!__DEV__) return;
  seq += 1;
  const r = PixelRatio.get();
  const b = bounds ?? { x: 0, y: 0, w: 0, h: 0 };
  console.log(
    'MIRA_FOCUS ' +
      JSON.stringify({
        seq,
        screen,
        element_id: elementId,
        bounds: {
          x: Math.round(b.x * r),
          y: Math.round(b.y * r),
          w: Math.round(b.w * r),
          h: Math.round(b.h * r),
        },
        ts: Date.now(),
      }),
  );
}
