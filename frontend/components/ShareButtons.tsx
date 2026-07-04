"use client";

export default function ShareButtons({
  title,
  onShare,
}: {
  title: string;
  onShare?: () => void;
}) {
  const handleShare = async () => {
    onShare?.();

    if (navigator.share) {
      try {
        await navigator.share({ title, url: window.location.href });
        return;
      } catch {
        // user cancelled or share failed — fall through to copy-link
      }
    }

    await navigator.clipboard.writeText(window.location.href);
    alert("링크가 복사됐어요!");
  };

  // Kakao 공유 버튼은 여기 추가 — Kakao Developers에서 발급받은 JS 키가
  // 필요해서 스킬이 대신 만들 수 없음. 키 받으면 Kakao.Share.sendDefault 붙이면 됨.

  return (
    <div className="flex gap-3">
      <button
        onClick={handleShare}
        className="rounded-lg bg-black px-4 py-2 text-white"
      >
        공유하기
      </button>
    </div>
  );
}
