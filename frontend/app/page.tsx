"use client";

import { useEffect, useState } from "react";
import AdSlot from "@/components/AdSlot";
import ShareButtons from "@/components/ShareButtons";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Weights = Record<string, number>;
type Option = { label: string; text: string; weights: Weights };
type Question = { id: number; text: string; hint?: string; options: Option[] };
type Content = { title: string; subtitle?: string; questions: Question[] };

type Book = {
  book: string;
  author: string;
  publisher: string;
  blurb: string;
  cover: string;
  buyLink: string;
  pubDate?: string;
  priceStandard?: number;
  priceSales?: number;
  categoryName?: string;
};
type Persona = {
  id: string;
  youtuber: string;
  profileImage?: string;
  channelUrl: string;
  subscribers: number;
  category: string;
  fanLabel: string;
  why: string;
  books: Book[];
};
type MatchResult = {
  match: Persona;
  runnersUp: { youtuber: string; category: string; fanLabel: string }[];
};

const RANK_BADGE = [
  { label: "1위", className: "bg-gradient-to-br from-amber-300 to-yellow-500 text-amber-950" },
  { label: "2위", className: "bg-gradient-to-br from-slate-200 to-slate-400 text-slate-700" },
  { label: "3위", className: "bg-gradient-to-br from-orange-300 to-amber-600 text-orange-950" },
];

function formatSubs(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(n % 10000 === 0 ? 0 : 1)}만명`;
  return `${n.toLocaleString()}명`;
}

function bookMeta(b: Book): string {
  const parts: string[] = [];
  if (b.pubDate) parts.push(`${b.pubDate.slice(0, 4)}년`);
  const price = b.priceSales || b.priceStandard;
  if (price) parts.push(`${price.toLocaleString()}원`);
  return parts.join(" · ");
}

// Aladin's category path is deep (e.g. "국내도서>소설>한국소설") — show the leaf.
function categoryLeaf(name?: string): string {
  if (!name) return "";
  const parts = name.split(">");
  return parts[parts.length - 1].trim();
}

export default function Home() {
  const [content, setContent] = useState<Content | null>(null);
  const [step, setStep] = useState(0);
  const [vector, setVector] = useState<Weights>({});
  const [done, setDone] = useState(false);
  const [result, setResult] = useState<MatchResult | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/content`)
      .then((res) => res.json())
      .then(setContent)
      .catch(() => {});
    fetch(`${API_URL}/api/view`, { method: "POST" }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!done) return;
    fetch(`${API_URL}/api/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vector }),
    })
      .then((res) => res.json())
      .then(setResult)
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [done]);

  if (!content) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="animate-pulse text-slate-400">불러오는 중...</p>
      </main>
    );
  }

  const handleAnswer = (weights: Weights) => {
    const next = { ...vector };
    for (const [k, v] of Object.entries(weights)) {
      next[k] = (next[k] || 0) + v;
    }
    setVector(next);

    if (step + 1 < content.questions.length) {
      setStep(step + 1);
    } else {
      setDone(true);
    }
  };

  const handleShare = () => {
    fetch(`${API_URL}/api/share`, { method: "POST" }).catch(() => {});
  };

  const handleRestart = () => {
    setStep(0);
    setVector({});
    setResult(null);
    setDone(false);
  };

  if (done) {
    if (!result) {
      return (
        <main className="flex min-h-screen items-center justify-center">
          <p className="animate-pulse text-slate-400">당신의 취향을 분석하는 중...</p>
        </main>
      );
    }
    const { match, runnersUp } = result;
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center gap-6 px-5 py-12">
        <header className="animate-fade-up flex flex-col items-center text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-400">
            Your Match
          </p>
          <h1 className="mt-2 text-sm text-slate-500">당신과 가장 잘 맞는 유튜버는</h1>
          <div className="mt-3 flex items-center gap-3">
            {match.profileImage && (
              <img
                src={match.profileImage}
                alt={match.youtuber}
                className="h-14 w-14 rounded-full object-cover shadow-md ring-2 ring-white"
              />
            )}
            <a
              href={match.channelUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-gradient-to-r from-indigo-600 to-fuchsia-600 bg-clip-text text-3xl font-extrabold text-transparent"
            >
              {match.youtuber}
            </a>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            {match.category} · 구독자 {formatSubs(match.subscribers)}
          </p>
        </header>

        <section className="animate-fade-up w-full rounded-3xl border border-white/60 bg-white/70 p-6 text-center shadow-xl shadow-indigo-100 backdrop-blur">
          <p className="text-base font-bold text-slate-900">“{match.fanLabel}”</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{match.why}</p>
        </section>

        <p className="animate-fade-up pt-2 text-sm font-semibold text-slate-700">
          이런 당신이 사랑할 책 TOP 3
        </p>

        <div className="flex w-full flex-col gap-5">
          {match.books.map((b, i) => (
            <article
              key={b.book + i}
              className="animate-fade-up rounded-3xl border border-white/60 bg-white/70 p-6 shadow-xl shadow-indigo-100 backdrop-blur"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <div className="flex gap-4">
                <span
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold shadow-sm ${
                    RANK_BADGE[i]?.className ?? "bg-slate-200 text-slate-600"
                  }`}
                >
                  {RANK_BADGE[i]?.label ?? `${i + 1}위`}
                </span>
                {b.cover ? (
                  <img
                    src={b.cover}
                    alt={b.book}
                    className="h-32 w-auto rounded-lg object-cover shadow-lg ring-1 ring-black/5"
                  />
                ) : (
                  <div className="flex h-32 w-24 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-100 to-fuchsia-100 text-3xl">
                    📖
                  </div>
                )}
                <div className="min-w-0 flex-1 text-left">
                  <h2 className="text-base font-bold text-slate-900">『{b.book}』</h2>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {b.author} · {b.publisher}
                  </p>
                  {bookMeta(b) && (
                    <p className="mt-1 text-xs text-slate-400">{bookMeta(b)}</p>
                  )}
                  {categoryLeaf(b.categoryName) && (
                    <span className="mt-2 inline-block rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-500">
                      {categoryLeaf(b.categoryName)}
                    </span>
                  )}
                </div>
              </div>
              {b.blurb && (
                <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-slate-600">
                  {b.blurb}
                </p>
              )}
              <a
                href={b.buyLink}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-1 rounded-full bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
              >
                책 보러가기 →
              </a>
            </article>
          ))}
        </div>

        {runnersUp?.length > 0 && (
          <p className="animate-fade-up text-xs text-slate-400">
            이런 유튜버와도 잘 맞아요 · {runnersUp.map((r) => r.youtuber).join(" · ")}
          </p>
        )}

        <div className="flex w-full items-center justify-center gap-3">
          <ShareButtons title={content.title} onShare={handleShare} />
          <button
            onClick={handleRestart}
            className="rounded-full border border-slate-300 bg-white/70 px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm backdrop-blur transition hover:border-slate-400 hover:bg-white"
          >
            다시하기
          </button>
        </div>

        <AdSlot />
      </main>
    );
  }

  const question = content.questions[step];
  const progress = ((step + 1) / content.questions.length) * 100;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-7 px-5 py-12">
      <div>
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-400">
          <span>
            질문 {step + 1} / {content.questions.length}
          </span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200/70">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div key={step} className="animate-fade-up">
        <h1 className="text-2xl font-bold leading-snug text-slate-900">
          {question.text}
        </h1>
        {question.hint && (
          <p className="mt-2 text-sm leading-relaxed text-slate-400">{question.hint}</p>
        )}
      </div>

      <div key={`opts-${step}`} className="animate-fade-up flex flex-col gap-3">
        {question.options.map((opt) => (
          <button
            key={opt.label}
            onClick={() => handleAnswer(opt.weights)}
            className="group rounded-2xl border border-white/60 bg-white/70 px-5 py-4 text-left text-slate-700 shadow-sm shadow-indigo-100/50 backdrop-blur transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-md hover:shadow-indigo-200"
          >
            <span className="mr-2 font-bold text-indigo-400 group-hover:text-indigo-600">
              {opt.label}
            </span>
            {opt.text}
          </button>
        ))}
      </div>
    </main>
  );
}
