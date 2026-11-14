export function Alert({ title, children }: { title: string; children?: string }) {
  return (
    <div role="alert" className="rounded-2xl border border-[#e7c7c3] bg-[#fdf4f2] px-4 py-3 text-sm text-[#6f2c28]">
      <p className="font-semibold">{title}</p>
      {children ? <p className="mt-1">{children}</p> : null}
    </div>
  );
}
