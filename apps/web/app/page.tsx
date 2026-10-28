import { getApiBaseUrl } from "@/lib/config";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-4 px-4">
      <h1 className="text-3xl font-semibold">Sesli Mülakat Koçu</h1>
      <p className="text-neutral-600 dark:text-neutral-400">
        Geliştirme aşamasında. İş ilanına göre sesli mülakat pratiği yakında burada.
      </p>
      <p className="text-xs text-neutral-500">API: {getApiBaseUrl()}</p>
    </main>
  );
}
