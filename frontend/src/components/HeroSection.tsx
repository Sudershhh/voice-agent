import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Phone, Zap, Globe, Clock, Mic } from "lucide-react";
import { Plane, Hotel, UtensilsCrossed, Calendar } from "lucide-react";
import Silk from "@/components/Silk";

interface HeroSectionProps {
  onStartCall: () => void;
  isConnecting: boolean;
}

const features = [
  {
    icon: Plane,
    title: "Flight Planning",
    description: "Find and compare flights",
  },
  {
    icon: Hotel,
    title: "Hotels",
    description: "Discover accommodations",
  },
  {
    icon: UtensilsCrossed,
    title: "Restaurants",
    description: "Find dining options",
  },
  {
    icon: Calendar,
    title: "Itineraries",
    description: "Plan your journey",
  },
];

const stats = [
  {
    icon: Clock,
    value: "Minutes",
    label: "Plan trips in",
    description: "Fast planning",
  },
  {
    icon: Globe,
    value: "1000+",
    label: "Destinations",
    description: "Global coverage",
  },
  {
    icon: Zap,
    value: "Real-time",
    label: "Updates",
    description: "Live information",
  },
];

const trustIndicators = [
  { icon: Mic, text: "Voice-First" },
];

export function HeroSection({ onStartCall, isConnecting }: HeroSectionProps) {
  return (
    <div className="relative min-h-screen">
      {/* Silk background */}
      <div className="absolute inset-0 z-0">
        <Silk
          speed={5}
          scale={1}
          color="#5227FF"
          noiseIntensity={1.5}
          rotation={0}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 h-screen flex flex-col items-center justify-center text-center p-6 md:p-8">
        <div className="w-full max-w-2xl mx-auto flex flex-col items-center gap-6 md:gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="space-y-3 md:space-y-4"
          >
            <div className="space-y-2">
              <div className="text-sm md:text-base font-semibold text-white/90 tracking-wide uppercase">
                Paradise AI
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-tight">
                Plan Your Perfect Trip
              </h1>
            </div>
            <p className="text-lg md:text-xl text-white/80 leading-relaxed">
              Paradise AI is your intelligent travel planning voice agent that
              helps you discover flights, hotels, restaurants, and create
              complete itineraries
            </p>
          </motion.div>

          {/* Trust Indicators */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="flex flex-wrap justify-center gap-3"
          >
            {trustIndicators.map((indicator) => {
              const Icon = indicator.icon;
              return (
                <div
                  key={indicator.text}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 border border-white/20"
                >
                  <Icon className="h-3.5 w-3.5 text-white" />
                  <span className="text-xs font-medium text-white">
                    {indicator.text}
                  </span>
                </div>
              );
            })}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="pt-2"
          >
            <Button
              onClick={onStartCall}
              disabled={isConnecting}
              size="sm"
              className="gap-2 text-base md:text-base px-6 md:px-8 py-2 h-auto bg-white text-primary hover:bg-white/90 transition-all duration-200 hover:shadow-lg"
            >
              <Phone className="h-5 w-5" />
              {isConnecting ? "Connecting..." : "Start Call"}
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="pt-2 md:pt-4 w-full max-w-xl"
          >
            <div className="grid grid-cols-2 gap-4 md:gap-6">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.4 + index * 0.1 }}
                    className="flex flex-col items-center text-center space-y-1.5 md:space-y-2"
                  >
                    <div className="p-2.5 md:p-3 rounded-lg bg-white/10 text-white w-fit">
                      <Icon className="h-5 w-5 md:h-6 md:w-6" />
                    </div>
                    <div>
                      <h3 className="text-xs md:text-sm font-semibold text-white">
                        {feature.title}
                      </h3>
                      <p className="text-xs text-white/80">
                        {feature.description}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
