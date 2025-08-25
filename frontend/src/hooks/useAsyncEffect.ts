import { useEffect, useRef, useCallback } from 'react';

/**
 * Hook for handling async operations with proper cleanup
 * Prevents memory leaks from async operations that complete after component unmount
 */
export function useAsyncEffect(
  asyncOperation: () => Promise<void>,
  deps: React.DependencyList,
  onError?: (error: Error) => void
) {
  const isMountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  const executeAsync = useCallback(async () => {
    // Cancel any pending operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      if (isMountedRef.current) {
        await asyncOperation();
      }
    } catch (error) {
      if (isMountedRef.current && error instanceof Error) {
        if (error.name !== 'AbortError') {
          onError?.(error);
        }
      }
    }
  }, [asyncOperation, onError]);

  useEffect(() => {
    executeAsync();
  }, [executeAsync, ...deps]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);
}

/**
 * Hook for cancellable async operations
 * Returns a function that can be called to cancel the operation
 */
export function useCancellableAsync<T extends any[], R>(
  asyncFunction: (...args: T) => Promise<R>
): [(...args: T) => Promise<R | null>, () => void] {
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const execute = useCallback(async (...args: T): Promise<R | null> => {
    // Cancel previous operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new controller
    abortControllerRef.current = new AbortController();

    try {
      const result = await asyncFunction(...args);
      
      // Check if component is still mounted and operation wasn't cancelled
      if (isMountedRef.current && !abortControllerRef.current.signal.aborted) {
        return result;
      }
      return null;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return null;
      }
      throw error;
    }
  }, [asyncFunction]);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return [execute, cancel];
}

/**
 * Hook for handling intervals with proper cleanup
 */
export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<() => void>();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval
  useEffect(() => {
    function tick() {
      if (savedCallback.current) {
        savedCallback.current();
      }
    }
    
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

/**
 * Hook for handling event listeners with automatic cleanup
 */
export function useEventListener<K extends keyof WindowEventMap>(
  eventType: K,
  handler: (event: WindowEventMap[K]) => void,
  element: Window | Document | HTMLElement = window
) {
  const savedHandler = useRef<(event: WindowEventMap[K]) => void>();

  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!element || !element.addEventListener) return;

    const eventListener = (event: Event) => {
      if (savedHandler.current) {
        savedHandler.current(event as WindowEventMap[K]);
      }
    };

    element.addEventListener(eventType, eventListener);

    return () => {
      element.removeEventListener(eventType, eventListener);
    };
  }, [eventType, element]);
}