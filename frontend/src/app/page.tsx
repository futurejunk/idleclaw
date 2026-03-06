"use client";

import { useState } from "react";
import { LandingHero } from "@/components/landing/landing-hero";
import { ChatContainer } from "@/components/chat/chat-container";

export default function Home() {
  const [showHero, setShowHero] = useState(true);

  return (
    <>
      <ChatContainer onLogoClick={() => setShowHero(true)} />
      {showHero && (
        <LandingHero
          onDismiss={() => setShowHero(false)}
        />
      )}
    </>
  );
}
