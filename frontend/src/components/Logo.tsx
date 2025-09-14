"use client";

export default function Logo() {
  return (
    <img 
      src="/brand/logo-wordmark.svg" 
      alt="Ultimate Fantasy" 
      className="hidden h-6 w-auto md:block" 
      onError={(e) => ((e.currentTarget.style.display = 'none'))} 
    />
  );
}
