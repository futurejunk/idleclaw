"use client";

import { useState, useRef } from "react";
import { LandingHero } from "@/components/landing/landing-hero";
import { ChatContainer } from "@/components/chat/chat-container";

export default function Home() {
  const [showHero, setShowHero] = useState(() => {
    if (typeof window === "undefined") return true;
    return sessionStorage.getItem("idleclaw:chatActive") !== "1";
  });
  const hasBeenDismissed = useRef(!showHero);

  const handleDismiss = () => {
    hasBeenDismissed.current = true;
    sessionStorage.setItem("idleclaw:chatActive", "1");
    setShowHero(false);
  };

  return (
    <>
      <ChatContainer onLogoClick={() => {
        sessionStorage.removeItem("idleclaw:chatActive");
        setShowHero(true);
      }} />
      {showHero && (
        <LandingHero
          onDismiss={handleDismiss}
          entering={hasBeenDismissed.current}
        />
      )}
    </>
  );
}
