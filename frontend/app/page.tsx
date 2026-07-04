"use client";

import { useEffect, useState } from "react";
import AdSlot from "@/components/AdSlot";
import ShareButtons from "@/components/ShareButtons";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Option = { label: string; text: string; tag: string };
type Question = { id: number; text: string; options: Option[] };
type Result = {
  book: string;
  author: string;
  publisher: string;
  blurb: string;
  buyLink: string;
};
type Content = {
  title: string;
  questions: Question[];
};

export default function Home() {
  const [content, setContent] = useState<Content | null>(null);
  const [step, setStep] = useState(0);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [resultTag, setResultTag] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/content`)
      .then((res) => res.json())
      .then(setContent)
      .catch(() => {});

    fetch(`${API_URL}/api/view`, { method: "POST" }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!resultTag) return;
    fetch(`${API_URL}/api/result/${resultTag}`)
      .then((res) => res.json())
      .then(setResult)
      .catch(() => {});
  }, [resultTag]);

  if (!content) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p>불러오는 중...</p>
      </main>
    );
  }

  const handleAnswer = (tag: string) => {
    const nextScores = { ...scores, [tag]: (scores[tag] || 0) + 1 };
    setScores(nextScores);

    if (step + 1 < content.questions.length) {
      setStep(step + 1);
    } else {
      const winner = Object.entries(nextScores).sort((a, b) => b[1] - a[1])[0][0];
      setResultTag(winner);
    }
  };

  const handleShare = () => {
    fetch(`${API_URL}/api/share`, { method: "POST" }).catch(() => {});
  };

  if (resultTag) {
    if (!result) {
      return (
        <main className="flex min-h-screen items-center justify-center">
          <p>책 고르는 중...</p>
        </main>
      );
    }
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 p-8 text-center">
        <p className="text-sm text-gray-500">당신에게 어울리는 책은</p>
        <h1 className="text-2xl font-bold">『{result.book}』</h1>
        <p className="text-sm text-gray-600">
          {result.author} 저 · {result.publisher}
        </p>
        <p className="text-base leading-relaxed">{result.blurb}</p>
        <a
          href={result.buyLink}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg border border-black px-4 py-2"
        >
          책 보러가기
        </a>
        <ShareButtons title={content.title} onShare={handleShare} />
        <AdSlot />
      </main>
    );
  }

  const question = content.questions[step];

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 p-8">
      <p className="text-sm text-gray-500">
        {step + 1} / {content.questions.length}
      </p>
      <h1 className="text-xl font-bold">{question.text}</h1>
      <div className="flex flex-col gap-3">
        {question.options.map((opt) => (
          <button
            key={opt.label}
            onClick={() => handleAnswer(opt.tag)}
            className="rounded-lg border px-4 py-3 text-left hover:bg-gray-50"
          >
            {opt.text}
          </button>
        ))}
      </div>
    </main>
  );
}
