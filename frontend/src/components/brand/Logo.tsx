export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="10" fill="#2563EB" />
      <path
        fill="#FFFFFF"
        d="M10.4 9.1h6.6l4.6 4.4v9.2c0 .8-.6 1.4-1.4 1.4H10.4c-.8 0-1.4-.6-1.4-1.4V10.5c0-.8.6-1.4 1.4-1.4Z"
      />
      <path fill="#2563EB" d="M16.8 9.3v3.8h4.2L16.8 9.3Z" />
      <circle cx="12.5" cy="16.3" r="1.15" fill="#2563EB" />
      <path d="M14.8 16.3h4.8" stroke="#2563EB" strokeWidth="1.35" strokeLinecap="round" />
      <circle cx="12.5" cy="19.2" r="1.15" fill="#93C5FD" />
      <path d="M14.8 19.2h3.6" stroke="#93C5FD" strokeWidth="1.35" strokeLinecap="round" />
      <circle cx="12.5" cy="22.1" r="1.15" fill="#93C5FD" />
      <path d="M14.8 22.1h2.6" stroke="#93C5FD" strokeWidth="1.35" strokeLinecap="round" />
    </svg>
  );
}
