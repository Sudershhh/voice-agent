import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Phone } from "lucide-react";
import {
  Plane,
  Hotel,
  UtensilsCrossed,
  Calendar,
} from "lucide-react";

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

export function HeroSection({ onStartCall, isConnecting }: HeroSectionProps) {
  return (
    <div className="h-screen flex items-center justify-center p-6 md:p-8">
      <div className="w-full max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-6 md:space-y-8"
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="space-y-3 md:space-y-4"
          >
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground tracking-tight leading-tight">
              Plan Your Perfect Trip
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Your AI travel planning voice agent that helps you discover flights, hotels, restaurants, and create complete itineraries
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex justify-center pt-2"
          >
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                onClick={onStartCall}
                disabled={isConnecting}
                size="lg"
                className="gap-2 text-base md:text-lg px-6 md:px-8 py-5 md:py-6 h-auto"
              >
                <Phone className="h-5 w-5" />
                {isConnecting ? "Connecting..." : "Start Call"}
              </Button>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="pt-4 md:pt-6"
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 max-w-4xl mx-auto">
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
                    <div className="p-2.5 md:p-3 rounded-lg bg-primary/10 text-primary">
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
      </div>
    </div>
  );
}

