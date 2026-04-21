export default function Loader() {
  return (
    <div className="flex items-center justify-center h-48 text-brand-muted text-sm font-mono">
      Loading...
    </div>
  )
}

export function ErrorMsg({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center h-24 text-brand-bear text-sm font-mono">
      {message ?? 'Lỗi tải data'}
    </div>
  )
}
