import Link from "next/link";

export default function Home() {
  return (
    <section className="space-y-12 pb-10">
      <div className="rounded-3xl border border-slate-200 bg-white/95 p-8 shadow-sm sm:p-12">
        <div className="max-w-3xl space-y-6">
          <p className="inline-flex rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-teal-700">
            Responsible AI For Production Teams
          </p>
          <h1 className="font-display text-4xl font-bold leading-tight text-slate-900 sm:text-6xl">
            BiasX-Ray uncovers hidden discrimination in ML systems.
          </h1>
          <p className="max-w-2xl text-lg text-slate-600">
            Upload your dataset or model outcomes, detect unfair treatment across
            intersectional groups, simulate what-if scenarios, and get clear
            recommendations for mitigation.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/upload"
              className="rounded-xl bg-teal-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-teal-700"
            >
              Start Bias Scan
            </Link>
            <Link
              href="/dashboard"
              className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          {
            title: "Hidden Group Discovery",
            body: "Find unfair outcomes across single and intersectional segments like gender + region.",
          },
          {
            title: "Explainable Fairness",
            body: "Use Gemini to generate plain-English diagnoses and action-focused recommendations.",
          },
          {
            title: "What-If Simulator",
            body: "Explore how sensitive attributes affect model outcomes with side-by-side predictions.",
          },
        ].map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <h3 className="font-display text-xl font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
