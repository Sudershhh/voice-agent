import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Phone, Zap, Globe, Clock, Sparkles, Mic } from "lucide-react";
import { Plane, Hotel, UtensilsCrossed, Calendar } from "lucide-react";
import { World } from "@/components/ui/globe";
import type { GlobeConfig } from "@/components/ui/globe";

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
  { icon: Sparkles, text: "AI-Powered" },
  { icon: Mic, text: "Voice-First" },
];

// Travel-themed arc data connecting major destinations
const colors = ["#ec4899", "#f472b6", "#f9a8d4"];

const sampleArcs = [
  // Popular travel routes
  {
    order: 1,
    startLat: 40.7128,
    startLng: -74.006,
    endLat: 51.5072,
    endLng: -0.1276,
    arcAlt: 0.3,
    color: colors[0],
  },
  {
    order: 1,
    startLat: 34.0522,
    startLng: -118.2437,
    endLat: 40.7128,
    endLng: -74.006,
    arcAlt: 0.2,
    color: colors[1],
  },
  {
    order: 1,
    startLat: 35.6762,
    startLng: 139.6503,
    endLat: 22.3193,
    endLng: 114.1694,
    arcAlt: 0.2,
    color: colors[2],
  },
  {
    order: 2,
    startLat: 48.8566,
    startLng: 2.3522,
    endLat: 40.7128,
    endLng: -74.006,
    arcAlt: 0.3,
    color: colors[0],
  },
  {
    order: 2,
    startLat: 25.2048,
    startLng: 55.2708,
    endLat: 51.5072,
    endLng: -0.1276,
    arcAlt: 0.4,
    color: colors[1],
  },
  {
    order: 2,
    startLat: -33.8688,
    startLng: 151.2093,
    endLat: 35.6762,
    endLng: 139.6503,
    arcAlt: 0.5,
    color: colors[2],
  },
  {
    order: 3,
    startLat: 28.6139,
    startLng: 77.209,
    endLat: 51.5072,
    endLng: -0.1276,
    arcAlt: 0.3,
    color: colors[0],
  },
  {
    order: 3,
    startLat: 1.3521,
    startLng: 103.8198,
    endLat: 22.3193,
    endLng: 114.1694,
    arcAlt: 0.2,
    color: colors[1],
  },
  {
    order: 3,
    startLat: -22.9068,
    startLng: -43.1729,
    endLat: 40.7128,
    endLng: -74.006,
    arcAlt: 0.6,
    color: colors[2],
  },
  {
    order: 4,
    startLat: 55.7558,
    startLng: 37.6173,
    endLat: 48.8566,
    endLng: 2.3522,
    arcAlt: 0.2,
    color: colors[0],
  },
  {
    order: 4,
    startLat: 19.4326,
    startLng: -99.1332,
    endLat: 34.0522,
    endLng: -118.2437,
    arcAlt: 0.2,
    color: colors[1],
  },
  {
    order: 4,
    startLat: 31.2304,
    startLng: 121.4737,
    endLat: 35.6762,
    endLng: 139.6503,
    arcAlt: 0.1,
    color: colors[2],
  },
  {
    order: 5,
    startLat: -34.6037,
    startLng: -58.3816,
    endLat: 40.7128,
    endLng: -74.006,
    arcAlt: 0.7,
    color: colors[0],
  },
  {
    order: 5,
    startLat: 41.9028,
    startLng: 12.4964,
    endLat: 51.5072,
    endLng: -0.1276,
    arcAlt: 0.2,
    color: colors[1],
  },
  {
    order: 5,
    startLat: 37.7749,
    startLng: -122.4194,
    endLat: 34.0522,
    endLng: -118.2437,
    arcAlt: 0.1,
    color: colors[2],
  },
];

const globeConfig: GlobeConfig = {
  pointSize: 4,
  globeColor: "#fce7f3",
  showAtmosphere: true,
  atmosphereColor: "#fdf2f8",
  atmosphereAltitude: 0.1,
  emissive: "#f9a8d4",
  emissiveIntensity: 0.1,
  shininess: 0.9,
  polygonColor: "rgba(236,72,153,0.8)",
  ambientLight: "#fce7f3",
  directionalLeftLight: "#ffffff",
  directionalTopLight: "#ffffff",
  pointLight: "#ffffff",
  arcTime: 1000,
  arcLength: 0.9,
  rings: 1,
  maxRings: 3,
  initialPosition: { lat: 22.3193, lng: 114.1694 },
  autoRotate: true,
  autoRotateSpeed: 0.5,
};

export function HeroSection({ onStartCall, isConnecting }: HeroSectionProps) {
  return (
    <div className="h-screen flex items-center justify-center p-6 md:p-8">
      <div className="w-full max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 lg:gap-16 items-center">
          {/* Left Column: Content */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-4 md:space-y-6"
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="space-y-3 md:space-y-4"
            >
              <div className="space-y-2">
                <div className="text-sm md:text-base font-semibold text-primary tracking-wide uppercase">
                  Paradise AI
                </div>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground tracking-tight leading-tight">
                  Plan Your Perfect Trip
                </h1>
              </div>
              <p className="text-lg md:text-xl text-muted-foreground leading-relaxed">
                Paradise AI is your intelligent travel planning voice agent that helps you discover
                flights, hotels, restaurants, and create complete itineraries
              </p>
            </motion.div>

            {/* Trust Indicators */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="flex flex-wrap gap-3"
            >
              {trustIndicators.map((indicator) => {
                const Icon = indicator.icon;
                return (
                  <div
                    key={indicator.text}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/5 border border-primary/10"
                  >
                    <Icon className="h-3.5 w-3.5 text-primary" />
                    <span className="text-xs font-medium text-foreground">
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
                className="gap-2 text-base md:text-base px-6 md:px-8 py-2 h-auto transition-all duration-200 hover:opacity-90 hover:shadow-lg"
              >
                <Phone className="h-5 w-5" />
                {isConnecting ? "Connecting..." : "Start Call"}
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="pt-2 md:pt-4"
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
                      className="flex flex-col space-y-1.5 md:space-y-2"
                    >
                      <div className="p-2.5 md:p-3 rounded-lg bg-primary/10 text-primary w-fit">
                        <Icon className="h-5 w-5 md:h-6 md:w-6" />
                      </div>
                      <div>
                        <h3 className="text-xs md:text-sm font-semibold text-foreground">
                          {feature.title}
                        </h3>
                        <p className="text-xs text-muted-foreground">
                          {feature.description}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          </motion.div>

          {/* Right Column: Globe */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative w-full h-[350px] md:h-[450px] lg:h-[550px] md:ml-4 lg:ml-8"
          >
            <div className="absolute inset-0 w-full h-full">
              <World data={sampleArcs} globeConfig={globeConfig} />
            </div>
            <div className="absolute bottom-0 inset-x-0 h-20 bg-gradient-to-b pointer-events-none select-none from-transparent to-background z-40" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
