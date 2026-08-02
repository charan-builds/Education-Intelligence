"use client";

import { useEffect, useRef, useState } from "react";

type Options = {
  startedAtIso: string;
  totalSeconds: number;
  enabled: boolean;
  onExpire: () => void;
};

function getRemainingSeconds(startedAtIso: string, totalSeconds: number) {
  const startedAt = new Date(startedAtIso).getTime();
  const elapsedSeconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  return Math.max(0, totalSeconds - elapsedSeconds);
}

export function useDiagnosticCountdown({ startedAtIso, totalSeconds, enabled, onExpire }: Options) {
  const [remainingSeconds, setRemainingSeconds] = useState(() => getRemainingSeconds(startedAtIso, totalSeconds));
  const expiredRef = useRef(false);

  useEffect(() => {
    setRemainingSeconds(getRemainingSeconds(startedAtIso, totalSeconds));
    expiredRef.current = false;
  }, [startedAtIso, totalSeconds]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const tick = () => {
      const remaining = getRemainingSeconds(startedAtIso, totalSeconds);
      setRemainingSeconds(remaining);
      if (remaining <= 0 && !expiredRef.current) {
        expiredRef.current = true;
        onExpire();
      }
    };

    tick();
    const intervalId = window.setInterval(tick, 1000);
    return () => window.clearInterval(intervalId);
  }, [enabled, onExpire, startedAtIso, totalSeconds]);

  return remainingSeconds;
}

