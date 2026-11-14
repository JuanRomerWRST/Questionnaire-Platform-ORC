import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";

export function ProcessingError({
  message,
  retryAfter,
  onRetry,
}: {
  message: string;
  retryAfter?: number;
  onRetry: () => void;
}) {
  return (
    <div className="space-y-3">
      <Alert title={message}>{retryAfter ? `Puedes reintentar en ${retryAfter} segundos.` : undefined}</Alert>
      <Button type="button" variant="ghost" onClick={onRetry}>
        Reintentar
      </Button>
    </div>
  );
}
