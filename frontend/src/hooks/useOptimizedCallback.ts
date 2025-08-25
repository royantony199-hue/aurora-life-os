import { useCallback, useRef } from 'react';

/**
 * Optimized callback hook that prevents unnecessary re-renders
 * Only recreates the callback when dependencies actually change (deep comparison)
 */
export function useOptimizedCallback<T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T {
  const callbackRef = useRef<T>(callback);
  const depsRef = useRef<React.DependencyList>(deps);

  // Check if dependencies have actually changed
  const depsChanged = deps.length !== depsRef.current.length ||
    deps.some((dep, index) => dep !== depsRef.current[index]);

  if (depsChanged) {
    callbackRef.current = callback;
    depsRef.current = deps;
  }

  return useCallback(callbackRef.current, deps);
}

/**
 * Debounced callback hook for performance optimization
 * Useful for search inputs, API calls, etc.
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(((...args: any[]) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }) as T, [callback, delay, ...deps]);
}

/**
 * Throttled callback hook for performance optimization
 * Limits how frequently a function can be called
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList
): T {
  const lastRun = useRef<number>(0);

  return useCallback(((...args: any[]) => {
    const now = Date.now();
    if (now - lastRun.current >= delay) {
      callback(...args);
      lastRun.current = now;
    }
  }) as T, [callback, delay, ...deps]);
}