export function JsonViewer({ value }: { value: unknown }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-2xl bg-[#1c1915] p-4 text-xs leading-5 text-[#f3efe6]">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
