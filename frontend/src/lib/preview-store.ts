const DB_NAME = "qi";
const STORE = "source";
const KEY = "current";

let source: File | null = null;
let saved: Promise<void> = Promise.resolve();
const listeners = new Set<() => void>();

export function rememberPreview(file: File) {
  source = file;
  listeners.forEach((listener) => listener());
  saved = writeStoredFile(file);
}

export function sourceSaved(): Promise<void> {
  return saved;
}

export function readSourceFile(): File | null {
  return source;
}

export async function restoreSourceFile(): Promise<File | null> {
  if (source) return source;
  const stored = await readStoredFile();
  if (!stored) return null;
  source = stored;
  listeners.forEach((listener) => listener());
  return stored;
}

export function subscribePreview(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function withStore<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE)) request.result.createObjectStore(STORE);
    };
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const database = request.result;
      const operation = run(database.transaction(STORE, mode).objectStore(STORE));
      operation.onsuccess = () => {
        database.close();
        resolve(operation.result);
      };
      operation.onerror = () => {
        database.close();
        reject(operation.error);
      };
    };
  });
}

async function writeStoredFile(file: File) {
  try {
    await withStore("readwrite", (store) => store.put(file, KEY));
  } catch {
    // Sin almacenamiento local, repetir el archivo solo funciona en esta misma vista.
  }
}

async function readStoredFile(): Promise<File | null> {
  try {
    return await withStore("readonly", (store) => store.get(KEY));
  } catch {
    return null;
  }
}
