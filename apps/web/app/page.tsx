import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-4 px-4">
      <h1 className="text-3xl font-semibold">Sesli Mülakat Koçu</h1>
      <p className="text-neutral-600 dark:text-neutral-400">
        İş ilanını yapıştırın, ilana özel sorularla mülakat pratiği yapın. Şu an metin tabanlı
        çalışıyor; sesli mülakat ve değerlendirme raporu geliştirme aşamasında.
      </p>
      <Link
        href="/interview"
        className="self-start rounded-md bg-neutral-900 px-4 py-3 font-medium text-white dark:bg-neutral-100 dark:text-neutral-900"
      >
        Mülakata başla
      </Link>
    </main>
  );
}
